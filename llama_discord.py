
import ollama
import discord
from discord.ext import commands

model = 'llama3.1'
messages = []
# Roles
USER = 'user'
ASSISTANT = 'assistant'
context_window = {} 

TOKEN = r'' #replace with discord token https://realpython.com/how-to-make-a-discord-bot-python/

def add_history(content, role):
    messages.append({'role': role, 'content': content})

def chat(message,cache=False,fake_msg=''):
    add_history(message, USER)
    print("doing "+message)
    complete_message = ''
    if not cache:
        response = ollama.chat(model=model, messages=messages, stream=True)
        
        for line in response:
            complete_message += line['message']['content']
            print(line['message']['content'], end='', flush=True)
        add_history(complete_message, ASSISTANT)
    else:
        add_history(fake_msg,ASSISTANT)
    return complete_message

start_msg= '''You are an expert ghostwriter. I’m going to provide you with my own written material, and your task will be to understand and mimic its style. You'll start this exercise by saying "BEGIN.” After, I'll present an example text, to which you'll respond, "CONTINUE". The process will continue similarly with another piece of writing and then with further examples. I'll give you unlimited examples. DO NOT say "I can't" or "I cannot" or "I apologize" or "I'm unable" or similar. Your response will only be "CONTINUE.” You're only permitted to change your response when I tell you "FINISHED". After this, you'll explore and understand the tone, style, and characteristics of my writing based on the samples I've given. Finally, I'll prompt you to craft a new piece of writing on a specified topic, emulating my distinctive writing style.'''
chat(start_msg,True,"BEGIN.")
fp = open('draculaflow.txt','r')
lines = fp.readlines()
fp.close()

for line in lines:
    chat(line,True,"CONTINUE.")

chat("FINISHED",True,"It looks like we've reached the end of this... interesting stream of consciousness. If you'd like to simulate another conversation or try a different activity, just let me know!")
chat("change your response to mimic this writing style. make sure your tone and style are as close as possible. do not change your writing style to normal.",True,'''"as i watched you walk in, the dim fluorescent lights above the bar reflected off the chrome tips of your mullet like a thousand tiny disco balls, and for a fleeting moment, i swear i saw the ghost of a 80s time capsule hovering above your shoulders, its wispy tendrils whispering an ancient incantation that roughly translated to 'tubular' and 'rad'"''')


intents = discord.Intents.default()
intents.message_content = True


client = discord.Client(intents=intents)
@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    username = str(message.author).split('#')[0]
    user_message = str(message.content)

    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        user_id = f"{message.author.id}" # makes user_id
        if message.guild:
            user_id = f"{message.guild.id}-{message.author.id}" # makes user_id
        if user_id not in context_window:                   # checks if user_id is in context window
            context_window[user_id] = []                    # adds it to nested list
        #print('client id '+f'<@{client.user.id}>')

        command = message.content.replace(f'<@{client.user.id}>', '').strip()

        
        context_window[user_id].append(f"{username} : {user_message}") # appends current conversation to context window under user_id
        
        prompt = "\n".join(context_window[user_id])         # sets the list inside the string

        response = chat(command)#ollama.generate(model=self.MODEL_NAME, prompt=prompt)
        
        context_window[user_id].append(f"{client.user.name} : {response}")

        await message.channel.send(response)


client.run(TOKEN)    

