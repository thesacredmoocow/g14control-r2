import os
import re


def check_screen(config):  # Checks to see if the G14 has a 120Hz capable screen or not
    checkscreenref = str(os.path.join(config.get('temp_dir') + 'ChangeScreenResolution.exe'))
    screen = os.popen(checkscreenref + " /m /d=0")  # /m lists all possible resolutions & refresh rates
    output = screen.readlines()
    for line in output:
        if re.search("@120Hz", line):
            return True
    else:
        return False


def get_screen(config):  # Gets the current screen resolution
    getscreenref = str(os.path.join(config.get('temp_dir') + 'ChangeScreenResolution.exe'))
    screen = os.popen(getscreenref + " /l /d=0")  # /l lists current resolution & refresh rate
    output = screen.readlines()
    for line in output:
        if re.search("@120Hz", line):
            return True
    else:
        return False


def set_screen(config, user_settings, refresh, notification_callback=None, plugged_in=False, game_running=False):
    if check_screen(config):  # Before trying to change resolution, check that G14 is capable of 120Hz resolution
        user_settings.set("screen_hz", refresh, plugged_in=plugged_in, game_running=game_running)
        user_settings.set("name", "Custom", plugged_in=plugged_in, game_running=game_running)
        if refresh is None:
            set_screen(config, 120, plugged_in=plugged_in, game_running=game_running)  # If screen refresh rate is null (not set), set to default refresh rate of 120Hz
        checkscreenref = str(os.path.join(config.get('temp_dir') + 'ChangeScreenResolution.exe'))
        os.popen(
            checkscreenref + " /d=0 /f=" + str(refresh)
        )
        if notification_callback:
            notification_callback("Screen refresh rate set to: " + str(refresh) + "Hz", config.get('notification_time'))
    else:
        return
