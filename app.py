from flask import Flask, request, jsonify, session
from flask_cors import CORS
import json
import speech_recognition as sr
from ibm_watson import AssistantV2, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import dotenv
from ibm_cloud_sdk_core.api_exception import ApiException
import re

dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas
app.secret_key = os.urandom(24)  # Clave secreta para las sesiones

# Configuración de IBM Watson Assistant
assistant_apikey = os.getenv("ASSISTANT_APIKEY")
assistant_url = os.getenv("ASSISTANT_URL")
assistant_id = os.getenv("ASSISTANT_ID")

authenticator = IAMAuthenticator(assistant_apikey)
assistant = AssistantV2(
    version='2021-06-14',
    authenticator=authenticator
)
assistant.set_service_url(assistant_url)

# Configuración de IBM Watson Speech to Text
stt_apikey = os.getenv("STT_APIKEY")
stt_url = os.getenv("STT_URL")

stt_authenticator = IAMAuthenticator(stt_apikey)
speech_to_text = SpeechToTextV1(authenticator=stt_authenticator)
speech_to_text.set_service_url(stt_url)

recognizer = sr.Recognizer()

def clean_text(text):
    # Eliminar espacios adicionales y caracteres especiales no deseados
    text = re.sub(r'\s+', ' ', text)  # Reemplazar múltiples espacios por uno solo
    text = re.sub(r'[^\w\s]', '', text)  # Eliminar caracteres especiales
    return text.strip()

# Diccionario para convertir palabras a números
def words_to_numbers(text):
    number_dict = {
        "cero": "0", "uno": "1", "dos": "2", "tres": "3", "cuatro": "4",
        "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9",
        "diez": "10", "once": "11", "doce": "12", "trece": "13", "catorce": "14",
        "quince": "15", "dieciséis": "16", "diecisiete": "17", "dieciocho": "18", "diecinueve": "19",
        "veinte": "20", "treinta": "30", "cuarenta": "40", "cincuenta": "50",
        "sesenta": "60", "setenta": "70", "ochenta": "80", "noventa": "90",
        "cien": "100", "doscientos": "200", "trescientos": "300", "cuatrocientos": "400",
        "quinientos": "500", "seiscientos": "600", "setecientos": "700", "ochocientos": "800", "novecientos": "900",
        "mil": "1000"
    }
    words = text.split()
    result = []
    for word in words:
        if word in number_dict:
            result.append(number_dict[word])
        elif len(word) == 1 and word.isalpha():
            result.append(word)
        else:
            result.append(word)
    return ' '.join(result)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_input = data.get('message')
    session_id = data.get('session_id')

    try:
        if not session_id:
            # Crear una nueva sesión si no hay session_id
            session_response = assistant.create_session(
                assistant_id=assistant_id
            ).get_result()
            session_id = session_response['session_id']
            print(f"New session created: {session_id}")  # Depuración: Imprimir session_id

        response = assistant.message(
            assistant_id=assistant_id,
            session_id=session_id,
            input={
                'message_type': 'text',
                'text': words_to_numbers(user_input)
            }
        ).get_result()
        return jsonify({'response': response, 'session_id': session_id})
    except ApiException as ex:
        print(f"API Exception: {ex}")
        return jsonify({'error': str(ex)}), 500
    except Exception as e:
        print(f"General Exception: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/capture_voice', methods=['POST'])
def capture_voice():
    audio_file = request.files['file']
    audio_data = audio_file.read()
    session_id = request.form.get('session_id')
    try:
        stt_response = speech_to_text.recognize(
            audio=audio_data,
            content_type='audio/wav',
            model='es-ES_BroadbandModel'
        ).get_result()
        user_input = stt_response['results'][0]['alternatives'][0]['transcript']
        user_input = words_to_numbers(user_input)
        response = assistant.message(
            assistant_id=assistant_id,
            session_id=session_id,
            input={
                'message_type': 'text',
                'text': user_input
            }
        ).get_result()
        return jsonify({'response': response, 'session_id': session_id})
    except ApiException as ex:
        print(f"API Exception: {ex}")
        return jsonify({'error': str(ex)}), 500
    except Exception as e:
        print(f"General Exception: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)