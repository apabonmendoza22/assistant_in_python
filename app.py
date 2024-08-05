import json
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import dotenv
dotenv.load_dotenv()


assistant_apikey = os.getenv("ASSISTANT_APIKEY")
assistant_url = os.getenv("ASSISTANT_URL")
assistant_id = os.getenv("ASSISTANT_ID")

# Configura tus credenciales
authenticator = IAMAuthenticator(assistant_apikey)
assistant = AssistantV2(
    version='2021-06-14',
    authenticator=authenticator
)

# Asegúrate de que esta URL es correcta para tu instancia
assistant.set_service_url(assistant_url)

try:
    # Crear una nueva sesión
    session_response = assistant.create_session(
        assistant_id= assistant_id  # Verifica que este ID es correcto
    ).get_result()
    session_id = session_response['session_id']
    print(f"Session ID: {session_id}")

    while True:
        # Leer entrada del usuario
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'salir']:
            break

        # Enviar la entrada del usuario al chatbot
        response = assistant.message(
            assistant_id=assistant_id,  # Verifica que este ID es correcto
            session_id=session_id,
            input={
                'message_type': 'text',
                'text': user_input
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
        assistant_id=assistant_id,  # Verifica que este ID es correcto
        session_id=session_id
    )
except Exception as e:
    print(f"Error: {e}")