import requests
import os
import time
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0',port=8080)#8080

def check_availability():
    while True:
        try:
            r = requests.get('http://localhost:8080')#8080
            if r.status_code == 200:
                print('Bot is online.')
            else:
                print('Bot is offline. Restarting...')
                os.system('sudo ifconfig eth0 down && sudo ifconfig eth0 up')
                Thread(target=run).start()
        except:
            print('Bot is offline. Restarting...')
            os.system('sudo ifconfig eth0 down && sudo ifconfig eth0 up')
            Thread(target=run).start()
        time.sleep(10)

def keep_alive():
    t = Thread(target=run)
    t.start()
    Thread(target=check_availability).start()