import { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './Login.css';

export default function Login({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isLogin
        ? `${API_BASE_URL}/api/login`
        : `${API_BASE_URL}/api/register`;
      const response = await axios.post(endpoint, {
        username,
        password,
      });

      onLogin(response.data.token, response.data.username);
    } catch (err) {
      setError(err.response?.data?.error || 'Error en la solicitud');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>🎮 Juego del Pájaro</h1>
        <h2>{isLogin ? 'Iniciar Sesión' : 'Registrarse'}</h2>

        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Usuario"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Cargando...' : isLogin ? 'Ingresar' : 'Registrarse'}
          </button>
        </form>

        <p className="toggle">
          {isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}{' '}
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            style={{
              background: 'none',
              color: '#ff6b6b',
              padding: 0,
              margin: 0,
            }}
          >
            {isLogin ? 'Registrate' : 'Inicia sesión'}
          </button>
        </p>
      </div>
    </div>
  );
}
