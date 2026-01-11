import { useState, useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './Game.css';

export default function Game({ username, token, onLogout }) {
  const canvasRef = useRef(null);
  const [points, setPoints] = useState(0);
  const [shots, setShots] = useState(0);
  const [hits, setHits] = useState(0);
  const [leaderboard, setLeaderboard] = useState([]);
  const [showLeaderboard, setShowLeaderboard] = useState(false);

  // Array de pájaros aleatorios
  const birdsRef = useRef([]);

  const createBird = (canvas) => ({
    x: Math.random() * (canvas.width - 100) + 50,
    y: Math.random() * (canvas.height - 100) + 50,
    width: 40,
    height: 40,
    vx: Math.random() * 2 + 0.5,
    vy: 0,
  });

  const socketRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Hacer que el canvas sea responsivo
    const resizeCanvas = () => {
      const wrapper = canvas.parentElement;
      canvas.width = wrapper.clientWidth;
      canvas.height = wrapper.clientHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Inicializar 5 pájaros aleatorios
    birdsRef.current = Array(5)
      .fill(null)
      .map(() => createBird(canvas));

    const ctx = canvas.getContext('2d');
    let animationId;
    let lastShotX = null;
    let lastShotY = null;
    let shotOpacity = 0;
    let currentMouseX = canvas.width / 2;
    let currentMouseY = canvas.height / 2;

    // Función para crear sonido de disparo
    const playShootSound = () => {
      const audioContext = new (window.AudioContext ||
        window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 800;
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(
        0.01,
        audioContext.currentTime + 0.1
      );

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    };

    socketRef.current = io(API_BASE_URL, {
      extraHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });

    socketRef.current.on('disparo', () => {
      setShots((prev) => prev + 1);

      // Disparo automático del sensor desde donde está el crosshair
      const shotX = currentMouseX;
      const shotY = currentMouseY;

      lastShotX = shotX;
      lastShotY = shotY;
      shotOpacity = 1;

      playShootSound();

      // Revisar colisión con todos los pájaros
      birdsRef.current.forEach((bird, index) => {
        const distance = Math.sqrt(
          Math.pow(shotX - bird.x, 2) + Math.pow(shotY - bird.y, 2)
        );

        if (distance < bird.width / 2 + 25) {
          setHits((prev) => prev + 1);
          setPoints((prev) => prev + 10);

          // Regenerar pájaro en nueva posición aleatoria
          birdsRef.current[index] = createBird(canvas);

          socketRef.current.emit('hit', { points: 10 });
          console.log('¡ACIERTO DEL SENSOR!');
        }
      });
    });

    socketRef.current.on('connect', () => {
      console.log('✓ Conectado al servidor WebSocket');
    });

    const drawBird = (bird) => {
      ctx.fillStyle = '#FFD700';
      ctx.beginPath();
      ctx.arc(bird.x, bird.y, bird.width / 2, 0, Math.PI * 2);
      ctx.fill();

      // Ojo del pájaro
      ctx.fillStyle = 'black';
      ctx.beginPath();
      ctx.arc(bird.x + 10, bird.y - 5, 3, 0, Math.PI * 2);
      ctx.fill();

      // Pico del pájaro
      ctx.strokeStyle = 'orange';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(bird.x + 15, bird.y);
      ctx.lineTo(bird.x + 25, bird.y);
      ctx.stroke();
    };

    const drawCrosshair = () => {
      const centerX = currentMouseX;
      const centerY = currentMouseY;
      const size = 30;

      ctx.strokeStyle = 'rgba(255, 0, 0, 0.6)';
      ctx.lineWidth = 2;

      // Líneas del crosshair
      ctx.beginPath();
      ctx.moveTo(centerX - size, centerY);
      ctx.lineTo(centerX + size, centerY);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(centerX, centerY - size);
      ctx.lineTo(centerX, centerY + size);
      ctx.stroke();

      // Círculo central
      ctx.beginPath();
      ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
      ctx.stroke();
    };

    const drawShotIndicator = () => {
      if (lastShotX !== null && lastShotY !== null && shotOpacity > 0) {
        ctx.fillStyle = `rgba(255, 0, 0, ${shotOpacity})`;
        ctx.beginPath();
        ctx.arc(lastShotX, lastShotY, 20, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = `rgba(255, 100, 100, ${shotOpacity})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(lastShotX, lastShotY, 25, 0, Math.PI * 2);
        ctx.stroke();

        shotOpacity -= 0.02;
      }
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Fondo
      ctx.fillStyle = 'rgba(100, 150, 255, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Dibujar todos los pájaros
      birdsRef.current.forEach((bird) => {
        drawBird(bird);

        // Animar cada pájaro
        bird.x += bird.vx;
        bird.y += bird.vy + Math.sin(Date.now() * 0.01) * 0.5;

        if (bird.x > canvas.width + 50) {
          bird.x = -50;
        }

        if (bird.y < 0) bird.y = 0;
        if (bird.y > canvas.height) bird.y = canvas.height;
      });

      // Dibujar crosshair
      drawCrosshair();

      // Dibujar indicador de disparo
      drawShotIndicator();

      animationId = requestAnimationFrame(animate);
    };

    animate();

    // Manejar movimiento del joystick - el crosshair sigue el mouse por todo el canvas
    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      currentMouseX = e.clientX - rect.left;
      currentMouseY = e.clientY - rect.top;
    };

    const handleTouchMove = (e) => {
      if (e.touches.length > 0) {
        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        currentMouseX = touch.clientX - rect.left;
        currentMouseY = touch.clientY - rect.top;
      }
    };

    const handleCanvasClick = (e) => {
      // Click manual del usuario dispara desde la posición del mouse
      lastShotX = currentMouseX;
      lastShotY = currentMouseY;
      shotOpacity = 1;

      setShots((prev) => prev + 1);
      playShootSound();

      // Revisar colisión con todos los pájaros
      birdsRef.current.forEach((bird, index) => {
        const distance = Math.sqrt(
          Math.pow(currentMouseX - bird.x, 2) +
            Math.pow(currentMouseY - bird.y, 2)
        );

        if (distance < bird.width / 2 + 25) {
          setHits((prev) => prev + 1);
          setPoints((prev) => prev + 10);

          // Regenerar pájaro en nueva posición aleatoria
          birdsRef.current[index] = createBird(canvas);

          socketRef.current.emit('hit', { points: 10 });
        }
      });
    };

    canvas.addEventListener('click', handleCanvasClick);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('touchmove', handleTouchMove);

    return () => {
      cancelAnimationFrame(animationId);
      canvas.removeEventListener('click', handleCanvasClick);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('resize', resizeCanvas);
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [token]);

  const loadLeaderboard = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/leaderboard`);
      setLeaderboard(response.data);
      setShowLeaderboard(!showLeaderboard);
    } catch (err) {
      console.error('Error cargando leaderboard:', err);
    }
  };

  const saveScore = async () => {
    try {
      await axios.post(
        `${API_BASE_URL}/api/score/record`,
        {
          username,
          points,
          shots,
          hits,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      alert('¡Puntuación guardada!');
    } catch (err) {
      console.error('Error guardando puntuación:', err);
    }
  };

  const handleLogoutClick = () => {
    saveScore();
    onLogout();
  };

  return (
    <div className="game-container">
      <div className="header">
        <h1>🎮 Juego del Pájaro</h1>
        <div className="user-info">
          <span>👤 {username}</span>
          <button onClick={handleLogoutClick} className="logout-btn">
            Salir
          </button>
        </div>
      </div>

      <div className="game-content">
        <div className="canvas-wrapper">
          <canvas ref={canvasRef} className="game-canvas" />
        </div>

        <div className="stats">
          <div className="stat">
            <span>🎯 Puntos:</span>
            <strong>{points}</strong>
          </div>
          <div className="stat">
            <span>🔫 Disparos:</span>
            <strong>{shots}</strong>
          </div>
          <div className="stat">
            <span>✅ Aciertos:</span>
            <strong>{hits}</strong>
          </div>
          <div className="stat">
            <span>📊 Precisión:</span>
            <strong>
              {shots > 0 ? ((hits / shots) * 100).toFixed(1) : 0}%
            </strong>
          </div>
        </div>

        <div className="buttons">
          <button onClick={saveScore} className="save-btn">
            💾 Guardar Puntuación
          </button>
          <button onClick={loadLeaderboard} className="leaderboard-btn">
            🏆 Leaderboard
          </button>
        </div>

        {showLeaderboard && (
          <div className="leaderboard">
            <h2>🏆 Top 10</h2>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Usuario</th>
                  <th>Puntos</th>
                  <th>Aciertos</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((score, index) => (
                  <tr
                    key={index}
                    className={score.username === username ? 'your-score' : ''}
                  >
                    <td>{index + 1}</td>
                    <td>{score.username}</td>
                    <td>{score.points}</td>
                    <td>{score.hits}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
