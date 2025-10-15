import UniversalSpeech as u_speech
_speech_engine = None
try:    
    _speech_engine = u_speech.UniversalSpeech()        
    _speech_engine.enable_native_speech(False)        
    print(f"Screen reader detected: {_speech_engine.engine_used}")
except Exception as e:    
    print(f"Failed to initialize UniversalSpeech engine: {e}")
    _speech_engine = None
def speak(msg: str, interrupt: bool = True):
    if _speech_engine:
        try:            
            _speech_engine.say(msg, interrupt)
        except Exception as e:
            print(f"Error while trying to speak: {e}")
    else:        
        print(f"Speech engine not available. Message: '{msg}'")