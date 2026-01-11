# 🎮 Juego del Pájaro - Sistema Distribuido con PIR

Un juego interactivo donde los sensores PIR disparan contra un pájaro volador. Incluye autenticación de usuarios, persistencia en MongoDB y leaderboard en tiempo real.

## 🏗️ Arquitectura

```
alarma/
├── backend/              # Flask API
│   ├── app.py           # Servidor principal
│   ├── requirements.txt  # Dependencias
│   └── .env            # Variables de entorno
├── frontend/            # React app
│   ├── src/
│   ├── public/
│   └── package.json
├── templates/           # HTML heredado
├── server.py           # Servidor heredado
├── alarm.py            # ESP32 MicroPython
└── server_simple.py    # Servidor simple (deprecated)
```

## 🚀 Instalación

### Backend (Flask)

```bash
cd backend
pip install -r requirements.txt
python app.py
```

El servidor estará en `http://localhost:5000`

### Frontend (React)

```bash
cd frontend
npm install
npm start
```

La app estará en `http://localhost:3000`

## 🔧 Configuración

### Variables de Entorno

Crea un archivo `.env` en `backend/`:

```
MONGO_URI=mongodb+srv://byron:VXIoVz6pWE1wA32Y@casino.9ylyhg2.mongodb.net/casino?appName=casino
PORT=5000
SECRET_KEY=tu-clave-secreta-cambiar-en-produccion
```

## 📱 API Endpoints

### Autenticación

- **POST** `/api/register` - Registrar nuevo usuario
- **POST** `/api/login` - Iniciar sesión

### Juego

- **GET** `/api/score` - Obtener puntuación actual
- **POST** `/api/score/record` - Guardar puntuación
- **GET** `/api/leaderboard` - Obtener top 10

### Salud

- **GET** `/api/health` - Verificar estado

## 🎯 Características

✅ Autenticación JWT
✅ MongoDB para persistencia
✅ WebSocket para eventos en tiempo real
✅ Sensor PIR que dispara eventos
✅ Juego con pájaro volador
✅ Leaderboard global
✅ Interfaz moderna con React

## 📡 WebSocket Events

### Cliente → Servidor

- `hit` - Cuando haces clic en el pájaro

### Servidor → Cliente

- `disparo` - Cuando el sensor PIR detecta movimiento
- `status` - Estado de conexión

## 🔌 Integración ESP32

El ESP32 enviará eventos MQTT cuando detecte movimiento:

```python
# alarm.py
client.publish(b"seguridad.movimiento", b"ALERTA")
```

Estos eventos se convertirán en WebSocket `disparo` en el frontend.

## 🐛 Troubleshooting

### "Not Found" en el frontend

- Verifica que React está en puerto 3000
- Verifica que Flask está en puerto 5000

### MongoDB connection error

- Verifica la `MONGO_URI` en `.env`
- Asegúrate que la IP está whitelisted en MongoDB Atlas

### Sensor PIR no se conecta

- Verifica RabbitMQ está corriendo
- Verifica que el usuario `admin:admin` existe en RabbitMQ
- Verifica que la IP del servidor es correcta en `alarm.py`

## 📊 Próximas Features

- [ ] Multijugador en tiempo real
- [ ] Diferentes niveles de dificultad
- [ ] Efectos de sonido y partículas
- [ ] Badges y logros
- [ ] Histórico de partidas

## 📝 Licencia

MIT
