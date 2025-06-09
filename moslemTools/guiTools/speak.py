import os
import ctypes
dll_path = os.path.join(os.getcwd(), "data", "dlls")
os.add_dll_directory(dll_path)
nvda = ctypes.windll.LoadLibrary(os.path.join(dll_path, "nvda_speak.dll"))
def speak(msg):
    running = nvda.nvdaController_testIfRunning()
    if running != 1:
        nvda.nvdaController_speakText(msg)