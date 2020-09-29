import os


def set_ryzenadj(config, user_settings, tdp, notification_callback=None, plugged_in=False, game_running=False):
    user_settings.set("cpu_tdp", tdp, plugged_in=plugged_in, game_running=game_running)
    user_settings.set("name", "Custom", plugged_in=plugged_in, game_running=game_running)
    ryzenadj = str(os.path.join(config.get('temp_dir') + "ryzenadj.exe"))
    if tdp is None:
        return
    else:
        os.popen(
            ryzenadj + " -a " + str(tdp) + " -b " + str(tdp)
        )
        if notification_callback:
            notification_callback("setting TDP to " + str(float(tdp) / 1000) + "W", config.get('notification_time'))


def get_ryzenadj(config, tdp, notification_callback=None):
    ryzenadj = str(os.path.join(config.get('temp_dir') + "ryzenadj.exe"))
    if tdp is None:
        return
    else:
        os.popen(
            ryzenadj + " -a " + str(tdp) + " -b " + str(tdp)
        )
        if notification_callback:
            notification_callback("setting TDP to " + str(float(tdp) / 1000) + "W", config.get('notification_time'))
