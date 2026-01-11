import pika
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder="templates", static_folder="templates")
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")


# --- Rutas de Flask ---
@app.route("/")
def index():
    print("✓ Sirviendo index.html")
    return render_template("index.html")


@app.route("/test")
def test():
    return {"status": "OK"}


# --- Lógica de RabbitMQ ---
def callback(ch, method, properties, body):
    mensaje = body.decode()
    print(f" [x] Recibido desde ESP: {mensaje}")
    try:
        socketio.emit(
            "alerta_movimiento",
            {"msg": "¡Movimiento Detectado! - " + time.strftime("%H:%M:%S")},
            namespace="/",
        )
    except Exception as e:
        print(f"Error emitiendo: {e}")


def consume_rabbit():
    try:
        credentials = pika.PlainCredentials("admin", "admin")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost", credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue="web_server_queue")
        channel.queue_bind(
            exchange="amq.topic",
            queue="web_server_queue",
            routing_key="seguridad.movimiento",
        )
        channel.basic_consume(
            queue="web_server_queue", on_message_callback=callback, auto_ack=True
        )
        print(" [*] Esperando mensajes de RabbitMQ...")
        channel.start_consuming()
    except Exception as e:
        print(f"Error RabbitMQ: {e}")


# --- Eventos WebSocket ---
@socketio.on("connect")
def handle_connect():
    print("✓ Cliente WebSocket conectado")
    emit("status", {"msg": "Conectado al servidor"})


@socketio.on("disconnect")
def handle_disconnect():
    print("✗ Cliente WebSocket desconectado")


if __name__ == "__main__":
    # Iniciamos RabbitMQ en un hilo separado
    t = threading.Thread(target=consume_rabbit, daemon=True)
    t.start()
    time.sleep(1)

    print("\n" + "=" * 60)
    print("🚀 Servidor INICIADO")
    print("📍 Accede desde el navegador a:")
    print("   http://192.168.101.9:5000")
    print("=" * 60 + "\n")

    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
