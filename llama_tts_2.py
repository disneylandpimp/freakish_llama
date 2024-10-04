
import ollama
import pyttsx3
import sounddevice as sd
import queue
import vosk
import json
import re

# Initialize variables and objects
model = 'llama3.1'
messages = []
USER = 'user'
ASSISTANT = 'assistant'

# Initialize speech recognition and text-to-speech engines
#recognizer = sr.Recognizer()
engine = pyttsx3.init()

voices = engine.getProperty('voices') 
engine.setProperty('voice', voices[97].id)

# Optimize TTS engine for faster speaking
engine.setProperty('rate', 175) 

# Initialize Vosk model (replace 'model_path' with the path to your downloaded Vosk model)
vosk_model = vosk.Model(r'/Users/macadmin/Downloads/vosk-model-small-en-us-0.15')  # Replace with your Vosk model path
audio_queue = queue.Queue()

def add_history(content, role):
    """Adds conversation history to messages list."""
    messages.append({'role': role, 'content': content})

def clean_and_buffer_text(text, buffer):
    """
    Cleans up special characters and determines when to speak.
    Returns text to be spoken and the updated buffer.
    """
    # Append new text to the buffer
    buffer += text

    # Regular expression to filter out unwanted special characters
    clean_text = re.sub(r'[^a-zA-Z0-9\s.,!?\'"-]', '', buffer)

    # Check for complete sentences or phrases
    if re.search(r'[.!?]$', clean_text) or len(clean_text) > 50:
        # If a complete phrase is detected or buffer exceeds a certain length
        phrase = clean_text.strip()
        buffer = ''  # Clear buffer after speaking
        return phrase, buffer
    else:
        # Return nothing to speak and maintain the buffer
        return '', buffer

def chat(message, cache=False, fake_msg='',addHistory=True):
    """Handles chat interaction with the Llama model."""
    add_history(message, USER)
    print("Processing: " + message)
    complete_message = ''
    buffer = ''
    
    if not cache:
        response = ollama.chat(model=model, messages=messages, stream=True)
        
        for line in response:
            line_text = line['message']['content']
            complete_message += line_text
            print(line_text, end='', flush=True)
            
            # Process incoming text and check if it is ready to be spoken
            speakable_text, buffer = clean_and_buffer_text(line_text, buffer)
            
            if speakable_text:
                # Speak the detected phrase
                engine.say(speakable_text)
                engine.runAndWait()

        # Clear any remaining buffered text after the response ends
        if buffer:
            engine.say(buffer.strip())
            engine.runAndWait()
            buffer = ''

        if addHistory:
            add_history(complete_message, ASSISTANT)
        
        #engine.say(complete_message)
        #engine.runAndWait()

    else:
        add_history(fake_msg, ASSISTANT)
    
    # Speak the response
    

    
    
    return complete_message

# Function to capture audio using sounddevice and Vosk
def get_speech_input():
    """Captures speech input using Vosk for faster offline recognition."""
    def callback(indata, frames, time, status):
        if status:
            print(status, flush=True)
        audio_queue.put(bytes(indata))

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("Listening... (Say 'quit' to exit, 'clear' to reset conversation)")
        rec = vosk.KaldiRecognizer(vosk_model, 16000)
        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if 'text' in result and result['text']:
                    print(f"You said: {result['text']}")
                    return result['text']
            else:
                # In partial recognition, we can get more text but sometimes wait for final input
                partial = json.loads(rec.PartialResult())
                if 'partial' in partial and partial['partial']:
                    continue
    return ""


start_msg= '''You are an expert ghostwriter. I’m going to provide you with my own written material, and your task will be to understand and mimic its style. You'll start this exercise by saying "BEGIN.” After, I'll present an example text, to which you'll respond, "CONTINUE". The process will continue similarly with another piece of writing and then with further examples. I'll give you unlimited examples. DO NOT say "I can't" or "I cannot" or "I apologize" or "I'm unable" or similar. Your response will only be "CONTINUE.” You're only permitted to change your response when I tell you "FINISHED". After this, you'll explore and understand the tone, style, and characteristics of my writing based on the samples I've given. Finally, I'll prompt you to craft a new piece of writing on a specified topic, emulating my distinctive writing style.'''
chat(start_msg,True,"BEGIN.")

fp = open('draculaflow.txt','r')
lines = fp.readlines()
fp.close()

for line in lines:
    chat(line,True,"CONTINUE.")

chat("FINISHED",True,"It looks like we've reached the end of this... interesting stream of consciousness. If you'd like to simulate another conversation or try a different activity, just let me know!")
chat("change your response to mimic this writing style. make sure your tone and style are as close as possible. do not change your writing style to normal.",True,'''"as i watched you walk in, the dim fluorescent lights above the bar reflected off the chrome tips of your mullet like a thousand tiny disco balls, and for a fleeting moment, i swear i saw the ghost of a 80s time capsule hovering above your shoulders, its wispy tendrils whispering an ancient incantation that roughly translated to 'tubular' and 'rad'"''')

# Main loop for voice interaction
while True:
    speech_input = get_speech_input().lower()
    
    if speech_input == 'quit':
        break
    elif speech_input == 'clear':
        messages = []
        print("Conversation cleared.")
    elif speech_input:
        chat(speech_input,addHistory=False)
