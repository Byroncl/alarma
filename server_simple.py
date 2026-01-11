#!/usr/bin/env python3
import pika
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os

# Obtener la ruta del directorio actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Configuración
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config["SECRET_KEY"] = "secret!"
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    engineio_logger=False,
    logger=False,
)

print(f"[Config] Base dir: {BASE_DIR}")
print(f"[Config] Template dir: {TEMPLATE_DIR}")
print(f"[Config] Template exists: {os.path.exists(TEMPLATE_DIR)}")
print(
    f"[Config] index.html exists: {os.path.exists(os.path.join(TEMPLATE_DIR, 'index.html'))}"
)


# --- Rutas de Flask ---
@app.route("/")
def index():
    print("✓ GET / - Sirviendo index.html")
    try:
        return render_template("index.html")
    except Exception as e:
        print(f"✗ Error al renderizar: {e}")
        return {"error": str(e)}, 500


@app.route("/health")
def health():
    return {"status": "OK"}, 200


# --- Lógica de RabbitMQ ---
def callback(ch, method, properties, body):
    mensaje = body.decode()
    print(f"[RabbitMQ] Recibido: {mensaje}")
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
            pika.ConnectionParameters(
                host="localhost",
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
        )
        channel = connection.channel()

        # Purgar y eliminar la cola antigua si existe
        try:
            channel.queue_purge(queue="web_server_queue")
            channel.queue_delete(queue="web_server_queue")
            print("[RabbitMQ] Cola antigua eliminada")
        except:
            pass

        # Crear la nueva cola sin durable
        channel.queue_declare(queue="web_server_queue", durable=False)
        channel.queue_bind(
            exchange="amq.topic",
            queue="web_server_queue",
            routing_key="seguridad.movimiento",
        )
        channel.basic_consume(
            queue="web_server_queue", on_message_callback=callback, auto_ack=True
        )
        print("[RabbitMQ] ✓ Esperando mensajes...")
        channel.start_consuming()
    except Exception as e:
        print(f"[RabbitMQ Error] {e}")
        time.sleep(5)
        consume_rabbit()


# --- Eventos WebSocket ---
@socketio.on("connect")
def handle_connect():
    print("✓ Cliente conectado")
    emit("status", {"msg": "Conectado al servidor"})


@socketio.on("disconnect")
def handle_disconnect():
    print("✗ Cliente desconectado")


if __name__ == "__main__":
    # Iniciamos RabbitMQ en un hilo separado
    t = threading.Thread(target=consume_rabbit, daemon=True)
    t.start()
    time.sleep(1)

    print("\n" + "=" * 70)
    print("🚀 SERVIDOR INICIADO")
    print("=" * 70)
    print("📍 Accede a: http://192.168.101.9:5000")
    print("=" * 70 + "\n")

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False,
    )
