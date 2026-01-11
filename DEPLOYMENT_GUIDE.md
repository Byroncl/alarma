# 📱 Guía de Despliegue en Red Local

## ✅ Cambios Realizados

1. **Joystick Removido** - La interfaz ahora solo muestra el crosshair sin el visual del joystick
2. **Múltiples Pájaros** - 5 pájaros aleatorios en el canvas con velocidades variadas
3. **Configuración de Red** - Backend y Frontend configurados para aceptar conexiones de red

---

## 🚀 Pasos para Acceder desde tu Celular

### 1. Obtener tu IP Local

En Windows, abre PowerShell y ejecuta:

```powershell
ipconfig
```

Busca el valor de "IPv4 Address" en la sección de tu red WiFi. Ejemplo:

```
IPv4 Address . . . . . . . . . . : 192.168.1.100
```

### 2. Iniciar el Backend

Desde `c:\Users\byron\Desktop\alarma\backend`:

```bash
python app.py
```

Deberías ver:

```
🚀 BACKEND INICIADO
📍 http://0.0.0.0:5000
```

### 3. Iniciar el Frontend (en otra terminal)

Desde `c:\Users\byron\Desktop\alarma\frontend`:

```bash
npm run dev
```

Verás algo como:

```
VITE v7.2.4  ready in XXX ms
➜  Local:   http://localhost:5174/
➜  Network: http://192.168.1.100:5174/
```

### 4. Abrir en tu Celular

- **En la misma WiFi**, abre navegador en tu celular
- Escribe la URL de Network que apareció: `http://192.168.1.100:5174/`
- ¡Listo! Deberías ver el login del juego

---

## ⚙️ Cómo Funciona

### Backend (Flask)

- Ya estaba configurado con `host="0.0.0.0"` ✅
- Acepta conexiones desde cualquier IP en el puerto 5000

### Frontend (Vite)

- Actualizado con `host: '0.0.0.0'` para aceptar conexiones externas
- Auto-detección de IP: El archivo `config.js` detecta automáticamente si es localhost o red

### Configuración (`frontend/src/config.js`)

```javascript
const hostname = window.location.hostname;
const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
export const API_BASE_URL = isLocalhost
  ? 'http://localhost:5000'
  : `http://${hostname}:5000`;
```

Esto significa:

- Si accedes desde `localhost:5174` → Backend en `localhost:5000`
- Si accedes desde `192.168.1.100:5174` → Backend en `192.168.1.100:5000` ✨

---

## 🎮 Cambios en el Juego

### Múltiples Pájaros

- Ahora hay **5 pájaros simultáneamente** en el canvas
- Cada uno tiene posición y velocidad aleatoria
- Se regeneran en nueva posición al ser alcanzados

### Sin Joystick

- Se removió el visual del joystick
- El crosshair rojo aún sigue tu mouse libremente
- Funcionan igual: clics para disparar + sensor PIR

---

## 🔧 Resolución de Problemas

### "No puedo conectar desde el celular"

1. Verifica que están en la **misma WiFi**
2. Asegúrate de que la IP es correcta (ver `npm run dev` en frontend)
3. Prueba acceder a `http://[IP]:5174/` (sin https)

### "El backend no se conecta"

1. Verifica que `app.py` está corriendo
2. Revisa que usas la misma IP en ambos lados
3. Si usas firewall, puede bloquear puertos 5000 y 5174

### "Funciona en localhost pero no en red"

1. Recarga la página en el celular con Ctrl+Shift+R (borrar cache)
2. Abre consola del navegador (F12) para ver errores
3. Verifica la URL en el Network tab del móvil

---

## 📝 Archivos Modificados

- ✅ `frontend/src/pages/Game.jsx` - Múltiples pájaros, sin joystick
- ✅ `frontend/src/pages/Login.jsx` - Usa config.js para API
- ✅ `frontend/vite.config.js` - Configurado para network
- ✅ `frontend/src/config.js` - NUEVO - Auto-detección de IP

---

## 🎯 Próximos Pasos Opcionales

Si quieres mejorar más:

1. Agregar nivel de dificultad (más pájaros en niveles altos)
2. Velocidades variables por pájaro
3. Efectos visuales al golpear
4. Sonido diferente para aciertos
