import os

from g14_system.util import parse_boolean, get_G14_dir


def get_dgpu():
    current_pwr = os.popen("powercfg /GETACTIVESCHEME")  # I know, it's ugly, but no other way to do that from py.
    pwr_guid = current_pwr.readlines()[0].rsplit(": ")[1].rsplit(" (")[0].lstrip("\n")  # Parse the GUID
    pwr_settings = os.popen(
        "powercfg /Q " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857"
    )  # Let's get the dGPU status in the current power scheme
    output = pwr_settings.readlines()  # We save the output to parse it afterwards
    dgpu_ac = parse_boolean(output[-3].rsplit(": ")[1].strip("\n"))  # Convert to boolean for "On/Off"
    return dgpu_ac


def set_dgpu(config, user_settings, state, notification_callback=None, plugged_in=False, game_running=False):
    user_settings.set("dgpu_enabled", state, plugged_in=plugged_in, game_running=game_running)
    user_settings.set("name", "Custom", plugged_in=plugged_in, game_running=game_running)
    current_pwr = os.popen("powercfg /GETACTIVESCHEME")  # Just to be safe, let's get the current power scheme
    pwr_guid = current_pwr.readlines()[0].rsplit(": ")[1].rsplit(" (")[0].lstrip("\n")  # Parse the GUID
    if state is True:  # Activate dGPU
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 2"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 2"
        )
        if notification_callback:
            notification_callback("dGPU ENABLED", config.get('notification_time'))  # Inform the user
    elif state is False:  # Deactivate dGPU
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 0"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 0"
        )
        os.system("\"" + get_G14_dir() + "\\restartGPUcmd.bat" + "\"")
        if notification_callback:
            notification_callback("dGPU DISABLED", config.get('notification_time'))  # Inform the user
