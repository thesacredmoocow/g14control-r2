import os
import time

from g14_system.util import set_power_plan


def get_boost():
    current_pwr = os.popen("powercfg /GETACTIVESCHEME")  # I know, it's ugly, but no other way to do that from py.
    pwr_guid = current_pwr.readlines()[0].rsplit(": ")[1].rsplit(" (")[0].lstrip("\n")  # Parse the GUID
    pwr_settings = os.popen(
        "powercfg /Q " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7"
    )  # Let's get the boost option in the currently active power scheme
    output = pwr_settings.readlines()  # We save the output to parse it afterwards
    ac_boost = output[-3].rsplit(": ")[1].strip("\n")  # Parsing AC, assuming the DC is the same setting
    # battery_boost = parse_boolean(output[-2].rsplit(": ")[1].strip("\n"))  # currently unused, we will set both
    return ac_boost


def set_boost(config, user_settings, state, dpp_GUID, app_GUID, notification_callback=None, plugged_in=False, game_running=False):
    user_settings.set("boost", state, plugged_in=plugged_in, game_running=game_running)
    user_settings.set("name", "Custom", plugged_in=plugged_in, game_running=game_running)
    # print(state)
    # print("GUID ", dpp_GUID)
    set_power_plan(config, dpp_GUID)
    current_pwr = os.popen("powercfg /GETACTIVESCHEME")  # Just to be safe, let's get the current power scheme
    pwr_guid = current_pwr.readlines()[0].rsplit(": ")[1].rsplit(" (")[0].lstrip("\n")  # Parse the GUID
    if state is True:  # Activate boost
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        if notification_callback:
            notification_callback("Boost ENABLED", config.get('notification_time'))  # Inform the user
    elif state is False:  # Deactivate boost
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        if notification_callback:
            notification_callback("Boost DISABLED", config.get('notification_time'))  # Inform the user
    elif state == 0:
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        if notification_callback:
            notification_callback("Boost DISABLED", config.get('notification_time'))  # Inform the user
    elif state == 4:
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        if notification_callback:
            notification_callback("Boost set to Efficient Aggressive",
                                  config.get('notification_time'))  # Inform the user
    elif state == 2:
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2"
        )
        if notification_callback:
            notification_callback("Boost set to Aggressive", config.get('notification_time'))  # Inform the user
    try:
        set_power_plan(config, app_GUID)
    except:
        print("Problem setting power plan for app_GUID %s" % app_GUID)
    time.sleep(0.25)
    try:
        set_power_plan(config, dpp_GUID)
    except:
        print("Problem setting power plan for dpp_GUID %s" % dpp_GUID)
