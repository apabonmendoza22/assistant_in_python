import json
import speech_recognition as sr
from ibm_watson import AssistantV2, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os 
import dotenv
dotenv.load_dotenv()

assistant_apikey = os.getenv("ASSISTANT_APIKEY")
assistant_url = os.getenv("ASSISTANT_URL")
assistant_id = os.getenv("ASSISTANT_ID")
stt_apikey = os.getenv("STT_APIKEY")
stt_url = os.getenv("STT_URL")


# Configura tus credenciales
authenticator = IAMAuthenticator(assistant_apikey)
assistant = AssistantV2(
    version='2021-06-14',
    authenticator=authenticator
)

# Asegúrate de que esta URL es correcta para tu instancia
assistant.set_service_url(assistant_url)

# Configura el servicio de Speech to Text
stt_authenticator = IAMAuthenticator(stt_apikey)
speech_to_text = SpeechToTextV1(authenticator=stt_authenticator)
speech_to_text.set_service_url(stt_url)

# Inicializar el reconocedor de voz
recognizer = sr.Recognizer()

try:
    # Crear una nueva sesión
    session_response = assistant.create_session(
        assistant_id=assistant_id  # Verifica que este ID es correcto
    ).get_result()
    session_id = session_response['session_id']
    print(f"Session ID: {session_id}")

    while True:
        # Capturar entrada de voz del usuario
        with sr.Microphone() as source:
            print("You: (habla ahora)")
            audio = recognizer.listen(source)

        try:
            # Convertir el audio a texto usando IBM Watson Speech to Text
            audio_data = audio.get_wav_data()
            stt_response = speech_to_text.recognize(
                audio=audio_data,
                content_type='audio/wav',
                model='es-ES_BroadbandModel'
            ).get_result()
            user_input = stt_response['results'][0]['alternatives'][0]['transcript']
            print(f"You: {user_input}")
        except Exception as e:
            print(f"Error al reconocer el audio: {e}")
            continue

        if user_input.lower() in ['exit', 'quit', 'salir']:
            break

        # Enviar la entrada del usuario al chatbot
        response = assistant.message(
            assistant_id=assistant_id,  # Verifica que este ID es correcto
            session_id=session_id,
            input={
                'message_type': 'text',
                'text': user_input,
                'options': {
                    'return_context': True,
                    'smart_formatting': True
                }
            }
        ).get_result()

        # Procesar la respuesta del chatbot
        if 'generic' in response['output']:
            for item in response['output']['generic']:
                if item['response_type'] == 'text':
                    print(f"Assistant: {item['text']}")
                elif item['response_type'] == 'suggestion':
                    print(item['title'])
                    for suggestion in item['suggestions']:
                        print(f"- {suggestion['label']}")

    # Cerrar la sesión
    assistant.delete_session(
        assistant_id='4de2c59b-4ee5-4bd4-a77a-61a061609898',  # Verifica que este ID es correcto
        session_id=session_id
    )
except Exception as e:
    print(f"Error: {e}")