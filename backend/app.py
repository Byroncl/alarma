#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
import pika
import threading

load_dotenv()

# Configuración
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "tu-clave-secreta-123")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 5000))

# Inicializar extensiones (sin Flask-CORS)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Conectar a MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database()
    users_collection = db["users"]
    scores_collection = db["scores"]
    print("✓ Conectado a MongoDB")
except Exception as e:
    print(f"✗ Error conectando a MongoDB: {e}")


# --- Middleware para CORS ---
@app.before_request
def handle_preflight():
    print(f"[CORS] {request.method} {request.path}")
    if request.method == "OPTIONS":
        print(f"[CORS] Handling OPTIONS request")
        return "", 200


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


# --- Funciones auxiliares ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token requerido"}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = data["user_id"]
        except:
            return jsonify({"error": "Token inválido"}), 401
        return f(current_user, *args, **kwargs)

    return decorated


def create_token(user_id):
    token = jwt.encode(
        {"user_id": str(user_id), "exp": datetime.utcnow() + timedelta(days=30)},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return token


@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username y password requeridos"}), 400

        if users_collection.find_one({"username": username}):
            return jsonify({"error": "Usuario ya existe"}), 400

        hashed_password = generate_password_hash(password)
        user = {
            "username": username,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
        }
        result = users_collection.insert_one(user)

        token = create_token(result.inserted_id)
        return (
            jsonify(
                {
                    "message": "Usuario creado exitosamente",
                    "token": token,
                    "user_id": str(result.inserted_id),
                    "username": username,
                }
            ),
            201,
        )
    except Exception as e:
        print(f"Error en register: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username y password requeridos"}), 400

        user = users_collection.find_one({"username": username})
        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Usuario o contraseña inválido"}), 401

        token = create_token(user["_id"])
        return (
            jsonify(
                {
                    "message": "Login exitoso",
                    "token": token,
                    "user_id": str(user["_id"]),
                    "username": username,
                }
            ),
            200,
        )
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"error": str(e)}), 500


# --- Rutas del juego ---
@app.route("/api/score", methods=["GET"])
@token_required
def get_score(current_user):
    from bson import ObjectId

    score = scores_collection.find_one({"user_id": ObjectId(current_user)})
    if score:
        return (
            jsonify(
                {
                    "points": score["points"],
                    "shots": score["shots"],
                    "hits": score["hits"],
                }
            ),
            200,
        )
    return jsonify({"points": 0, "shots": 0, "hits": 0}), 200


@app.route("/api/score/record", methods=["POST"])
@token_required
def record_score(current_user):
    from bson import ObjectId

    data = request.get_json()
    points = data.get("points", 0)
    shots = data.get("shots", 0)
    hits = data.get("hits", 0)

    user_id = ObjectId(current_user)
    score = scores_collection.find_one({"user_id": user_id})

    if score:
        scores_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "points": points,
                    "shots": shots,
                    "hits": hits,
                    "last_updated": datetime.utcnow(),
                }
            },
        )
    else:
        scores_collection.insert_one(
            {
                "user_id": user_id,
                "username": data.get("username", "unknown"),
                "points": points,
                "shots": shots,
                "hits": hits,
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow(),
            }
        )

    return jsonify({"message": "Puntuación guardada"}), 200


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    scores = list(scores_collection.find().sort("points", -1).limit(10))
    leaderboard = []
    for score in scores:
        leaderboard.append(
            {
                "username": score.get("username"),
                "points": score["points"],
                "hits": score["hits"],
            }
        )
    return jsonify(leaderboard), 200


# --- WebSocket para sensor PIR ---
def consume_rabbit():
    try:
        credentials = pika.PlainCredentials("admin", "admin")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost", credentials=credentials)
        )
        channel = connection.channel()

        try:
            channel.queue_purge(queue="web_server_queue")
            channel.queue_delete(queue="web_server_queue")
        except:
            pass

        channel.queue_declare(queue="web_server_queue", durable=False)
        channel.queue_bind(
            exchange="amq.topic",
            queue="web_server_queue",
            routing_key="seguridad.movimiento",
        )

        def callback(ch, method, properties, body):
            print("[PIR] Disparo detectado")
            socketio.emit(
                "disparo", {"timestamp": datetime.utcnow().isoformat()}, namespace="/"
            )

        channel.basic_consume(
            queue="web_server_queue", on_message_callback=callback, auto_ack=True
        )
        print("[RabbitMQ] ✓ Esperando disparos...")
        channel.start_consuming()
    except Exception as e:
        print(f"[RabbitMQ Error] {e}")


@socketio.on("connect")
def handle_connect():
    print("✓ Cliente WebSocket conectado")
    emit("status", {"msg": "Conectado al servidor"})


@socketio.on("disconnect")
def handle_disconnect():
    print("✗ Cliente WebSocket desconectado")


# --- Health check ---
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), 200


if __name__ == "__main__":
    # Iniciar RabbitMQ en un hilo
    t = threading.Thread(target=consume_rabbit, daemon=True)
    t.start()

    print("\n" + "=" * 70)
    print("🚀 BACKEND INICIADO")
    print("=" * 70)
    print(f"📍 http://localhost:{PORT}")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=PORT, debug=False)
