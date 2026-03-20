from flask import Flask
import os
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot Discord en ligne !"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
