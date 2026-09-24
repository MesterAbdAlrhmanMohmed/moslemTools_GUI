import os
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


def _get_sounds_dir():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "sounds")


def get_sound_file(direction):
    sounds_dir = _get_sounds_dir()
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
        try:
            player = _get_player()
            player.stop()
            player.setSource(QUrl.fromLocalFile(os.path.abspath(sound_path)))
            player.play()
        except Exception:
            pass
