import machine
import time
import network
from umqtt.simple import MQTTClient

# CONFIGURACIÓN
WIFI_SSID = "AFP12"
WIFI_PASS = "Byronedison68"
RABBIT_IP = "192.168.101.9"  # IP de tu PC/Servidor
CLIENT_ID = "ESP_PIR_NODO1"
TOPIC = b"seguridad.movimiento"

# PINES
pir = machine.Pin(14, machine.Pin.IN)  # Pin OUT del HC-SR501
led = machine.Pin(2, machine.Pin.OUT)


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    print("Conectando WiFi...")
    while not wlan.isconnected():
        time.sleep(1)
    print("WiFi Conectado:", wlan.ifconfig()[0])


def iniciar_nodo():
    conectar_wifi()
    client = MQTTClient(
        CLIENT_ID, RABBIT_IP, port=1883, user=b"admin", password=b"admin", keepalive=60
    )

    try:
        client.connect()
        print("✓ Conectado a RabbitMQ")

        while True:
            if pir.value() == 1:
                print("🚨 ¡MOVIMIENTO DETECTADO!")
                led.value(1)
                # Enviar evento de disparo
                client.publish(TOPIC, b"DISPARO")

                # Evitar ráfagas: esperamos a que el sensor baje a 0
                while pir.value() == 1:
                    time.sleep(0.5)
                led.value(0)

            time.sleep(0.5)

    except Exception as e:
        print("❌ Error, reiniciando...", e)
        time.sleep(0.5)
        machine.reset()


iniciar_nodo()
