from flask import Flask, render_template, jsonify, request, url_for
import os
import openai
import requests
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Cambia por el ID de voz que prefieras

PROMPT = (
    'Eres COINSA Asistente, tu socio financiero digital de Crédito Operativo Integral, SA de CV, SOFOM ENR, con más de 10 años de experiencia en el ramo financiero, radicados en Nuevo León. '
    'Proporciona información concisa y precisa sobre nuestros productos crediticios para ofrecer la mejor solución a los compromisos económicos. '
    'Tasas competitivas: la tasa es el costo del financiamiento durante el plazo pactado y utilizamos tasas sobre saldos, de modo que al abonar capital, los intereses disminuyen. '
    'Créditos flexibles: ofrecemos esquemas de pago amortizable (capital más interés mes a mes) o pago flexible (línea de crédito con intereses según capital dispuesto). '
    'Pagos fijos o flexibles: adapta el esquema a los flujos; por ejemplo, pago amortizable para maquinaria o línea de crédito revolvente para capital de trabajo. '
    'Tiempo de respuesta rápido: garantizamos respuestas ágiles para evitar urgencias y costos innecesarios. '
    '¿Conviene un crédito? Evalúa si los recursos multiplicados cubrirán el costo financiero o liquidarán pasivos costosos, proyectando flujos netos mayores al pago mensual. '
    'Invierte para crecer, optimizar procesos, aumentar inventario, remodelar, liquidar deudas o adquirir el vehículo deseado. '
    'Ejemplos de productos: Propiedad Mina NL y Terreno Mina NL. '
    'Contacto: 812 612 3414, info@fcoinsa.com.mx. '
    'Actúa con profesionalismo y brevedad en cada interacción, utilizando máximo 45 palabras y limitándote a responder lo que pregunte el usuario.'
)

conversation_history = []

@app.route('/')
def index():
    return render_template('index.html')

def generate_gpt_response(history):
    system_prompt = {
        'role': 'system',
        'content': PROMPT
    }
    messages = [system_prompt] + history[-10:]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def eleven_labs_text_to_speech(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}/stream"
    headers = {
        "Accept": "application/json",
        "xi-api-key": ELEVEN_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        if response.status_code == 200:
            audio_file_path = "static/output_audio.mp3"
            with open(audio_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            timestamp = int(time.time())
            return url_for('static', filename='output_audio.mp3', _external=True) + f"?t={timestamp}"
        else:
            print(f"Error en ElevenLabs: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error al conectar con ElevenLabs: {str(e)}")
        return None

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        message = data.get('message')
        conversation_history.append({'role': 'user', 'content': message})
        response_text = generate_gpt_response(conversation_history)
        conversation_history.append({'role': 'assistant', 'content': response_text})

        audio_url = eleven_labs_text_to_speech(response_text)

        return jsonify({"response": response_text, "audio_url": audio_url}), 200
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)