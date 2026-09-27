import os
import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

_player = None
_audio_output = None


def _get_player():
    global _player, _audio_output
    if _player is None:
        _player = QMediaPlayer()
        _audio_output = QAudioOutput()
        _player.setAudioOutput(_audio_output)
        _audio_output.setVolume(1.0)
    return _player


def get_sounds_dir():
    candidates = []
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(os.path.join(user_profile, "data", "sounds"))
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "data", "sounds"))
        candidates.append(os.path.join(exe_dir, "_internal", "data", "sounds"))
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "data", "sounds"))
    candidates.append(os.path.join(os.getcwd(), "data", "sounds"))
    cur = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        candidates.append(os.path.join(cur, "data", "sounds"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    for path in candidates:
        if os.path.isdir(path) and os.path.exists(path):
            return path
    if user_profile:
        fallback = os.path.join(user_profile, "data", "sounds")
        try:
            os.makedirs(fallback, exist_ok=True)
            return fallback
        except Exception:
            pass
    return candidates[0] if candidates else os.path.join("data", "sounds")


def _get_sounds_dir():
    return get_sounds_dir()


def get_sound_file(direction):
    sounds_dir = get_sounds_dir()
    setting_key = f"{direction}_page_file"
    try:
        from settings import settings_handler
        configured_name = settings_handler.get("page_turn_sound", setting_key)
        if configured_name:
            candidate = os.path.join(sounds_dir, configured_name)
            if os.path.exists(candidate):
                return candidate
    except Exception:
        pass
    prefix = f"{direction}_page."
    if os.path.exists(sounds_dir):
        for f in os.listdir(sounds_dir):
            if f.startswith(prefix):
                return os.path.join(sounds_dir, f)
    default_candidate = os.path.join(sounds_dir, f"{direction}_page.wav")
    if os.path.exists(default_candidate):
        return default_candidate
    return None


def play_page_turn_sound(direction="next", viewer_key=None):
    if viewer_key:
        try:
            from settings import settings_handler
            if settings_handler.get("page_turn_sound", viewer_key) == "False":
                return
        except Exception:
            pass
    sound_path = get_sound_file(direction)
    if sound_path and os.path.exists(sound_path):
        if sound_path.lower().endswith(".wav"):
            try:
                import winsound
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception:
                pass
        try:
            player = _get_player()
            player.stop()
            player.setSource(QUrl.fromLocalFile(os.path.abspath(sound_path)))
            player.play()
        except Exception:
            pass
