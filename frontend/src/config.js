// Configuración de la aplicación
// Cambia API_BASE_URL según donde despliegues el backend

// Para desarrollo local:
// export const API_BASE_URL = 'http://localhost:5000';

// Para acceso desde la red local (reemplaza 192.168.1.100 con tu IP):
// export const API_BASE_URL = 'http://192.168.1.100:5000';

// Auto-detección (recomendado para network):
const hostname = window.location.hostname;
const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
export const API_BASE_URL = isLocalhost
  ? 'http://localhost:5000'
  : `http://${hostname}:5000`;

console.log('API_BASE_URL:', API_BASE_URL);
