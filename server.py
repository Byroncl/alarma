import pika
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


# --- Lógica de RabbitMQ ---
def callback(ch, method, properties, body):
    print(f" [x] Recibido desde ESP: {body.decode()}")
    # Enviamos la alerta al navegador vía WebSockets
    socketio.emit("alerta_movimiento", {"msg": "¡Movimiento Detectado!"})


def consume_rabbit():
    credentials = pika.PlainCredentials("admin", "admin")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", credentials=credentials)
    )
    channel = connection.channel()
    # RabbitMQ MQTT plugin usa el exchange 'amq.topic' por defecto
    channel.queue_declare(queue="web_server_queue")
    channel.queue_bind(
        exchange="amq.topic",
        queue="web_server_queue",
        routing_key="seguridad.movimiento",
    )

    channel.basic_consume(
        queue="web_server_queue", on_message_callback=callback, auto_ack=True
    )
    print(" [*] Esperando mensajes. Para salir presiona CTRL+C")
    channel.start_consuming()


# --- Rutas de Flask ---
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # Iniciamos RabbitMQ en un hilo separado
    t = threading.Thread(target=consume_rabbit, daemon=True)
    t.start()
    # Iniciamos el servidor web
    socketio.run(app, host="0.0.0.0", port=5000)
