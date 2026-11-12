import asyncio
import io
import edge_tts
from flask import Flask, render_template_string, send_file, request

app = Flask(__name__)

ALLOWED_VOICES = {
    "es-ES-XimenaNeural": "Ximena (Colombia) - Recommended",
    "es-EC-AndreaNeural": "Andrea (Ecuador)",
    "es-MX-DaliaNeural": "Dalia (Mexico)",
    "es-ES-ElviraNeural": "Elvira (Spain)",
    "es-AR-ElenaNeural": "Elena (Argentina)",
    "es-ES-AlvaroNeural": "Alvaro (Spain)"
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Servicio Web - Alvaro</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f172a;
            color: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            background: #1e293b;
            padding: 2.5rem 2rem;
            border-radius: 1.25rem;
            text-align: center;
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
            border: 1px solid #334155;
            max-width: 480px;
            width: 100%;
            position: relative;
        }
        .badge {
            background: #0284c7;
            color: #ffffff;
            padding: 0.35rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 1.2rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        h1 {
            color: #38bdf8;
            font-size: 2.2rem;
            margin-bottom: 0.4rem;
            font-weight: 700;
        }
        .subtitle {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }
        .controls-group {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #334155;
            border-radius: 0.85rem;
            padding: 1.2rem;
            margin-bottom: 1.5rem;
        }
        .voice-label {
            display: block;
            font-size: 0.85rem;
            color: #94a3b8;
            margin-bottom: 0.5rem;
            text-align: left;
            font-weight: 500;
        }
        .voice-select {
            width: 100%;
            background: #0f172a;
            color: #f1f5f9;
            border: 1px solid #475569;
            border-radius: 0.5rem;
            padding: 0.6rem 0.8rem;
            font-size: 0.95rem;
            outline: none;
            cursor: pointer;
            transition: border-color 0.2s;
            margin-bottom: 1rem;
        }
        .voice-select:focus {
            border-color: #38bdf8;
        }
        .btn-action {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            gap: 8px;
            background: #0284c7;
            color: #ffffff;
            font-size: 1rem;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            border-radius: 0.65rem;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        }
        .btn-action:hover:not(:disabled) {
            background: #0369a1;
            transform: translateY(-2px);
        }
        .btn-action:disabled {
            background: #475569;
            color: #94a3b8;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .btn-pulse {
            animation: pulse-ring 2s infinite;
        }
        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(2, 132, 199, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(2, 132, 199, 0); }
            100% { box-shadow: 0 0 0 0 rgba(2, 132, 199, 0); }
        }
        .btn-retry {
            background: #dc2626;
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
        }
        .btn-retry:hover {
            background: #b91c1c;
        }
        .status-msg {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 0.75rem;
            line-height: 1.4;
        }
        .status-highlight {
            color: #38bdf8;
        }
        .footer {
            margin-top: 1.8rem;
            font-size: 0.9rem;
            color: #cbd5e1;
            border-top: 1px solid #334155;
            padding-top: 1.2rem;
            line-height: 1.5;
        }
        .footer strong {
            color: #38bdf8;
        }
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">Docker Engine • v1</span>
        <h1>¡Hola, Alvaro! 👋</h1>
        <p class="subtitle">Microservicio en Python 3.12 con Flask y Edge-TTS</p>
        
        <div class="controls-group">
            <label class="voice-label" for="voiceSelect">🎙️ Seleccionar voz (guardado automático):</label>
            <select id="voiceSelect" class="voice-select" onchange="changeVoice()">
                <option value="es-ES-XimenaNeural">Ximena (Colombia) ★ Predeterminada</option>
                <option value="es-EC-AndreaNeural">Andrea (Ecuador)</option>
                <option value="es-MX-DaliaNeural">Dalia (México)</option>
                <option value="es-ES-ElviraNeural">Elvira (España)</option>
                <option value="es-AR-ElenaNeural">Elena (Argentina)</option>
                <option value="es-ES-AlvaroNeural">Alvaro (España)</option>
            </select>

            <button id="btnGreeting" class="btn-action" onclick="playGreeting(false)">
                🔊 Saludo por voz
            </button>
            <button id="btnRetry" class="btn-action btn-retry" style="display: none;" onclick="playGreeting(false)">
                🔄 Error al cargar voz: Reintentar
            </button>
            <p id="statusMsg" class="status-msg"></p>
        </div>

        <audio id="audioElement" preload="auto"></audio>

        <div class="footer">
            Estudiante: <strong>Alvaro Becerra</strong><br>
            Servidor Remoto: 161.97.140.245
        </div>
    </div>

    <script>
        const audio = document.getElementById('audioElement');
        const btnGreeting = document.getElementById('btnGreeting');
        const btnRetry = document.getElementById('btnRetry');
        const voiceSelect = document.getElementById('voiceSelect');
        const statusMsg = document.getElementById('statusMsg');

        const COOLDOWN_DURATION_MS = 60 * 1000; // 1 minute cooldown for autoplay
        const KEY_LAST_PLAYED = 'last_played_timestamp';
        const KEY_PREFERRED_VOICE = 'preferred_voice';
        let retryTimeout = null;
        let countdownInterval = null;
        let interactionListenerAttached = false;

        function loadConfiguredVoice() {
            const savedVoice = localStorage.getItem(KEY_PREFERRED_VOICE);
            if (savedVoice && voiceSelect.querySelector(`option[value="${savedVoice}"]`)) {
                return savedVoice;
            }
            return 'es-ES-XimenaNeural';
        }

        voiceSelect.value = loadConfiguredVoice();

        function changeVoice() {
            localStorage.setItem(KEY_PREFERRED_VOICE, voiceSelect.value);
            playGreeting(false);
        }

        function showError() {
            btnGreeting.style.display = 'none';
            btnRetry.style.display = 'inline-flex';
            statusMsg.innerHTML = '<span style="color: #f87171;">⚠️ No se pudo generar el audio.</span>';
            if (retryTimeout) clearTimeout(retryTimeout);
            retryTimeout = setTimeout(() => {
                resetButton();
            }, 5000);
        }

        function resetButton() {
            btnRetry.style.display = 'none';
            btnGreeting.style.display = 'inline-flex';
            btnGreeting.disabled = false;
            btnGreeting.innerHTML = '🔊 Saludo por voz';
            updateCooldownStatus();
        }

        function updateCooldownStatus() {
            if (countdownInterval) clearInterval(countdownInterval);
            const lastPlayed = localStorage.getItem(KEY_LAST_PLAYED);
            if (!lastPlayed) {
                statusMsg.innerHTML = '💡 Autoplay activo para tu próxima recarga.';
                return;
            }

            function tick() {
                const now = Date.now();
                const elapsed = now - parseInt(lastPlayed);
                const remaining = COOLDOWN_DURATION_MS - elapsed;

                if (remaining > 0) {
                    const seconds = Math.ceil(remaining / 1000);
                    statusMsg.innerHTML = `⏱️ Autoplay en espera: <span class="status-highlight">${seconds}s</span> para sonar solo al recargar.`;
                } else {
                    statusMsg.innerHTML = '✨ ¡Listo! Al recargar sonará automáticamente.';
                    clearInterval(countdownInterval);
                }
            }
            tick();
            countdownInterval = setInterval(tick, 1000);
        }

        function playGreeting(isAutoplay = false) {
            if (retryTimeout) clearTimeout(retryTimeout);
            btnRetry.style.display = 'none';
            btnGreeting.style.display = 'inline-flex';
            btnGreeting.disabled = true;
            btnGreeting.classList.remove('btn-pulse');
            btnGreeting.innerHTML = '⏳ Reproduciendo...';

            const selectedVoice = voiceSelect.value;
            const targetUrl = `/audio-saludo?voice=${encodeURIComponent(selectedVoice)}`;
            if (!audio.src || !audio.src.includes(`voice=${encodeURIComponent(selectedVoice)}`)) {
                audio.src = targetUrl;
                audio.load();
            }

            audio.currentTime = 0;
            const playPromise = audio.play();

            if (playPromise !== undefined) {
                playPromise.then(() => {
                    localStorage.setItem(KEY_LAST_PLAYED, Date.now().toString());
                    if (countdownInterval) clearInterval(countdownInterval);
                    statusMsg.innerHTML = '🔊 Reproduciendo saludo con voz de Ximena...';
                }).catch(err => {
                    console.warn('Browser autoplay blocked:', err.name);
                    
                    if (isAutoplay) {
                        btnGreeting.disabled = false;
                        btnGreeting.classList.add('btn-pulse');
                        btnGreeting.innerHTML = '🔊 Toca aquí o en la pantalla';
                        statusMsg.innerHTML = '🔒 <em>El navegador pausó el sonido. Toca cualquier parte para escucharlo.</em>';

                        if (!interactionListenerAttached) {
                            interactionListenerAttached = true;
                            const enableAudio = () => {
                                document.removeEventListener('pointerdown', enableAudio);
                                document.removeEventListener('keydown', enableAudio);
                                playGreeting(false);
                            };
                            document.addEventListener('pointerdown', enableAudio, { once: true });
                            document.addEventListener('keydown', enableAudio, { once: true });
                        }
                    } else {
                        showError();
                    }
                });
            }
        }

        audio.onended = () => {
            resetButton();
        };

        audio.onerror = () => {
            showError();
        };

        window.addEventListener('DOMContentLoaded', () => {
            const lastPlayed = localStorage.getItem(KEY_LAST_PLAYED);
            const now = Date.now();

            const selectedVoice = voiceSelect.value;
            audio.src = `/audio-saludo?voice=${encodeURIComponent(selectedVoice)}`;

            if (!lastPlayed || (now - parseInt(lastPlayed)) >= COOLDOWN_DURATION_MS) {
                playGreeting(true);
            } else {
                resetButton();
            }
        });
    </script>
</body>
</html>
"""

async def generate_speech_audio(voice_name: str) -> bytes:
    communicator = edge_tts.Communicate(
        text="¡Hola Alvaro! Bienvenido a tu aplicación web.",
        voice=voice_name
    )
    audio_buffer = bytearray()
    async for chunk in communicator.stream():
        if chunk["type"] == "audio":
            audio_buffer.extend(chunk["data"])
    return bytes(audio_buffer)

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/audio-saludo")
def audio_greeting():
    voice = request.args.get("voice", "es-ES-XimenaNeural")
    if voice not in ALLOWED_VOICES:
        voice = "es-ES-XimenaNeural"
    try:
        audio_content = asyncio.run(generate_speech_audio(voice))
        return send_file(io.BytesIO(audio_content), mimetype="audio/mpeg")
    except Exception as error:
        return {"error": str(error)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
