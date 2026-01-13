from PyQt6.QtMultimedia import QMediaDevices, QAudioDevice
import settings
def get_audio_device(feature_name):        
    global_setting = settings.settings_handler.get("audio", "global")
    target_device_name = "Default"                
    if global_setting == "مخصص" or global_setting == "Custom":
        target_device_name = settings.settings_handler.get("audio", feature_name)
    elif global_setting and global_setting != "الافتراضي" and global_setting != "Default":
        target_device_name = global_setting            
    if target_device_name == "الافتراضي" or target_device_name == "Default" or not target_device_name:
        return QMediaDevices.defaultAudioOutput()            
    for device in QMediaDevices.audioOutputs():
        if device.description() == target_device_name:
            return device                
    return QMediaDevices.defaultAudioOutput()