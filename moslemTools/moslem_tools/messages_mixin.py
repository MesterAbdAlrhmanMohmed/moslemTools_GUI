import sys
import os
import threading
import random
import requests
import ujson as json
from settings import settings_handler, app
import guiTools
from .workers import MessageCheckWorker


class MessagesMixin:
    def start_message_check_thread(self):
        self.message_worker = MessageCheckWorker(self)
        self.message_worker.finished.connect(self.message_worker.deleteLater)
        self.message_worker.finished.connect(lambda: setattr(self, 'message_worker', None))
        thread = threading.Thread(target=self.message_worker.check_for_message)
        thread.daemon = True
        thread.start()

    def show_random_message(self):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "data", "json", "QuotesMessages.json")
        with open(file_path, "r", encoding="utf_8") as f:
            data = json.load(f)
        random_message = random.choice(data)
        guiTools.TextViewer(self, "رسالة لك", random_message).exec()

    def onViewLastMessageButtonClicked(self):
        with open(os.path.join(os.getenv('appdata'), settings_handler.appName, "message.json"), "r", encoding="utf-8") as file:
            data = json.load(file)
        guiTools.TextViewer(self, "آخر رسالة من المطور", data["message"]).exec()

    def whats_new_funktion(self):
        try:
            r = requests.get(f"https://raw.githubusercontent.com/MesterAbdAlrhmanMohmed/{settings_handler.appName}/main/{app.appdirname}/update/app.json")
            info = r.json()
            guiTools.TextViewer(self, "ما الجديد في آخر إصدار من البرنامج", info["what is new"]).exec()
        except Exception as e:
            print(e)
            guiTools.qMessageBox.MessageBox.error(self, "خطأ", "فشلت عملية جلب المعلومات, الرجاء الإتصال بالإنترنت")
