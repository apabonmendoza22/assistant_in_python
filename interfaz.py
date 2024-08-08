import json
import speech_recognition as sr
from ibm_watson import AssistantV2, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import dotenv
import tkinter as tk
from tkinter import scrolledtext

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
assistant.set_service_url(assistant_url)

stt_authenticator = IAMAuthenticator(stt_apikey)
speech_to_text = SpeechToTextV1(authenticator=stt_authenticator)
speech_to_text.set_service_url(stt_url)

recognizer = sr.Recognizer()

# Diccionario para convertir palabras a números
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

def words_to_numbers(text):
    text = text.lower()  # Convert text to lowercase
    words = text.split()
    result = []
    for word in words:
        if word in number_dict:
            result.append(number_dict[word])
        elif len(word) == 1 and word.isalpha():
            result.append(word)
        else:
            result.append(word)
    return ''.join(result)

def send_message():
    user_input = entry.get()
    if user_input.lower() in ['exit', 'quit', 'salir']:
        root.quit()
    else:
        response = assistant.message(
            assistant_id=assistant_id,
            session_id=session_id,
            input={
                'message_type': 'text',
                'text': words_to_numbers(user_input)
            }
        ).get_result()
        display_response(response)
        entry.delete(0, tk.END)

def capture_voice():
    with sr.Microphone() as source:
        text_area.insert(tk.END, "You: (habla ahora)\n")
        audio = recognizer.listen(source)
    try:
        audio_data = audio.get_wav_data(convert_rate=16000, convert_width=2)

        stt_response = speech_to_text.recognize(
            audio=audio_data,
            content_type='audio/wav',
            model='es-ES_BroadbandModel'
        ).get_result()

        user_input = stt_response['results'][0]['alternatives'][0]['transcript']
        user_input = words_to_numbers(user_input)
        text_area.insert(tk.END, f"You: {user_input}\n")
        entry.delete(0, tk.END)
        entry.insert(0, user_input)
        send_message()
    except Exception as e:
        text_area.insert(tk.END, f"Error al reconocer el audio: {e}\n")

def display_response(response):
    if 'generic' in response['output']:
        for item in response['output']['generic']:
            if item['response_type'] == 'text':
                text_area.insert(tk.END, f"Assistant: {item['text']}\n")
            elif item['response_type'] == 'suggestion':
                text_area.insert(tk.END, f"{item['title']}\n")
                for suggestion in item['suggestions']:
                    text_area.insert(tk.END, f"- {suggestion['label']}\n")

try:
    session_response = assistant.create_session(
        assistant_id=assistant_id
    ).get_result()
    session_id = session_response['session_id']
    print(f"Session ID: {session_id}")

    root = tk.Tk()
    root.title("Asistente de Voz")

    entry = tk.Entry(root, width=50)
    entry.pack(pady=10)

    send_button = tk.Button(root, text="Enviar", command=send_message)
    send_button.pack(pady=5)

    voice_button = tk.Button(root, text="Hablar", command=capture_voice)
    voice_button.pack(pady=5)

    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
    text_area.pack(pady=10)

    root.mainloop()

    assistant.delete_session(
        assistant_id=assistant_id,
        session_id=session_id
    )
except Exception as e:
    print(f"Error: {e}")