from datetime import datetime

import pystray
from PIL import Image
import time
import psutil
import resources
from threading import Thread
import MatrixController
import pywinusb.hid as hid
from g14_animatrix.flash_matrix import Flash
from g14_animatrix.weather_matrix import Weather
from g14_animatrix.ani_frame import point
from g14_system.atrofac import set_atrofac
from g14_system.boost import get_boost, set_boost
from g14_system.config import Config, UserSettings
from g14_system.dgpu import set_dgpu, get_dgpu
from g14_system.ryzenadj import set_ryzenadj
from g14_system.screen import get_screen, set_screen, check_screen
from g14_system.util import *

showFlash = False

animatrix_object = None
animatrix_enabled = False
animatrix_thread = None
animatrix_thread_running = False

newDotDelay = 80
threshold = 30
newDotCounter = 60
dotLength = 120
dot = point()
dots = []


def readData(data):
    if data[1] == 56:
        os.startfile(config.get('rog_key'))
    return None


def get_power_plans():
    dpp_GUID = None
    app_GUID = None
    all_plans = subprocess.check_output(["powercfg", "/l"])
    for i in str(all_plans).split('\\n'):
        if i.find(config.get('default_power_plan')) != -1:
            dpp_GUID = i.split(' ')[3]
        if i.find(config.get('alt_power_plan')) != -1:
            app_GUID = i.split(' ')[3]
    return dpp_GUID, app_GUID


def create_icon():
    if get_windows_theme() == 0:  # We will create the icon based on current windows theme
        return Image.open(os.path.join(config.get('temp_dir'), 'icon_light.png'))
    else:
        return Image.open(os.path.join(config.get('temp_dir'), 'icon_dark.png'))


def power_check():
    global auto_power_switch, ac, game_running
    if auto_power_switch:  # Only run while loop on startup if auto_power_switch is On (True)
        while True:
            new_ac_status = psutil.sensors_battery().power_plugged  # Get the current AC power status
            if ac != new_ac_status:
                ac = new_ac_status
                # if auto_power_switch:  # Check to user hasn't disabled auto_power_switch (i.e. by manually switching plans)
                plan = user_settings.get_plan(plugged_in=ac, game_running=game_running)
                if not plan:
                    if ac:  # If on AC power, and not on the default_ac_plan, switch to that plan
                        for preset_plan in config.get('plans', []):
                            if preset_plan['name'] == config.get("default_ac_plan", "Custom"):
                                plan = preset_plan
                                break
                    if not ac:  # If on DC power, and not on the default_dc_plan, switch to that plan
                        for preset_plan in config.get('plans', []):
                            if preset_plan['name'] == config.get("default_dc_plan", "Custom"):
                                plan = preset_plan
                                break

                apply_plan(plan)
                print("apply plan from power_check")
            time.sleep(config.get('check_power_every', []))
    else:
        return


def toggle_powerswitching(should_notify=False):
    global auto_power_switch
    auto_power_switch = not auto_power_switch
    config.set("enable_power_switching", auto_power_switch)
    if should_notify:
        notify("Auto power switching has been %s" % "ENABLED" if auto_power_switch else "DISABLED",
               config.get('notification_time'))


def gaming_check():  # Checks if user specified games/programs are running, and switches to user defined plan, then switches back once closed
    global default_gaming_plan_games, ac, game_running
    previous_plan = None  # Define the previous plan to switch back to

    while True:  # Continuously check every 10 seconds
        output = os.popen('wmic process get description, processid').read()
        process = output.split("\n")
        processes = set(i.split(" ")[0] for i in process)
        targets = set(default_gaming_plan_games)  # List of user defined processes
        if processes & targets:  # Compare 2 lists, if ANY overlap, set game_running to true
            new_game_running_state = True
        else:
            new_game_running_state = False
        if game_running != new_game_running_state:
            game_running = True
            plan = user_settings.get_plan(plugged_in=ac, game_running=game_running)
            if not plan:
                if game_running:  # If on AC power, and not on the default_ac_plan, switch to that plan
                    for preset_plan in config.get('plans', []):
                        if preset_plan['name'] == config.get("default_gaming_plan", "Silent (low-speed fan)"):
                            plan = preset_plan
                            break
                if not game_running:  # If on DC power, and not on the default_dc_plan, switch to that plan
                    for preset_plan in config.get('plans', []):
                        if preset_plan['name'] == config.get("default_starting_plan", "Silent (low-speed fan)"):
                            plan = preset_plan
                            break
            apply_plan(plan)
            print("apply plan from gaming_check")
        time.sleep(config.get('check_power_every'))


def notify(message, time):
    nt = Thread(target=do_notify, args=(message, time), daemon=True)
    nt.start()


def do_notify(message, sleep_time):
    global icon_app
    try:
        icon_app.notify(message)  # Display the provided argument as message
        # time.sleep(config.get('notification_time'))  # The message is displayed for the configured time. This is blocking.
        time.sleep(sleep_time)
        icon_app.remove_notification()  # Then, we will remove the notification
    except:
        return


# (["Disabled", "Enabled", "Aggressive", "Efficient Enabled", "Efficient Aggressive"][int(get_boost()[2:])])
def get_current():
    global ac, config, user_settings
    cpu_TDP = user_settings.get("cpu_tdp", 35000, plugged_in=ac, game_running=game_running)
    notify(
        "Plan: " + user_settings.get("name", "Custom", plugged_in=ac, game_running=game_running) + "\n" +
        "   dGPU: " + (["Off", "On"][get_dgpu()]) + "\n" +
        "   Boost: " + (["Disabled", "Enabled", "Aggressive", "Efficient Enabled", "Efficient Aggressive"][
            int(get_boost()[2:])]) + "\n" +
        "      TDP: " + str(float(cpu_TDP) / 1000) + "W" + "\n" +
        "   Refresh Rate: " + (["60Hz", "120Hz"][get_screen(config)]) + "\n" +
        "   Power: " + (["Battery", "AC"][bool(ac)]) + "\n" +
        "   Auto Switching: " + (["Off", "On"][auto_power_switch]) + "\n",
        config.get('long_notification_time')
    )  # Let's print the current values


def apply_plan(plan):
    global config, dpp_GUID, app_GUID, plugged_in, ac, game_running, icon_app
    print("Applying Plan...")
    plan_name = plan['name']
    set_atrofac(config, user_settings, plan['plan'], plan['cpu_curve'], plan['gpu_curve'], plugged_in=ac,
                game_running=game_running)
    set_dgpu(config, user_settings, plan['dgpu_enabled'], plugged_in=ac, game_running=game_running)
    set_screen(config, user_settings, plan['screen_hz'], plugged_in=ac, game_running=game_running)
    set_ryzenadj(config, user_settings, plan['cpu_tdp'], plugged_in=ac, game_running=game_running)
    set_boost(config, user_settings, plan["boost"], dpp_GUID, app_GUID, plugged_in=ac, game_running=game_running)
    apply_animatrix(user_settings.get("animatrix", None))
    user_settings.set("name", plan_name, plugged_in=ac, game_running=game_running)
    notify("Applied plan " + plan_name, config.get('notification_time'))


def get_plan_by_name(plan_name):
    for plan in config.get('plans', []):
        if plan['name'] == plan_name:
            return plan


def quit_app():
    global mc, use_animatrix, device
    if use_animatrix:
        mc.clearMatrix()
    icon_app.stop()  # This will destroy the the tray icon gracefully.
    print(device)
    device.close()
    try:
        sys.exit()
    except:
        print('System Exit')


def animatrix_thread_stop():
    global animatrix_thread, animatrix_thread_running, mc
    mc.clearMatrix()
    if animatrix_thread and animatrix_thread.is_alive() and animatrix_thread_running:
        animatrix_thread_running = False
        timeout = 1000
        while (animatrix_thread.is_alive() and timeout > 0):
            time.sleep(0.1)
            timeout -= 100


def animatrix_thread_start():
    global animatrix_thread, animatrix_thread_running
    if animatrix_thread:
        if animatrix_thread.is_alive():
            animatrix_thread_stop()
    animatrix_thread_running = True
    animatrix_thread = Thread(target=animatrix_object_thread, daemon=True)
    animatrix_thread.start()


def animatrix_object_thread():
    global animatrix_object
    frame_refresh_millis = 100
    while animatrix_thread_running and animatrix_object:
        currentTime = datetime.now()
        animatrix_object.updateFrame()
        render_time_millis = ((datetime.now() - currentTime).microseconds / 1000)
        time.sleep(max((frame_refresh_millis - render_time_millis) / 1000, 0))


def apply_animatrix(type=None):
    global config, animatrix_enabled, animatrix_object, mc, ac, game_running
    animatrix_thread_stop()
    user_settings.set("animatrix", type, plugged_in=ac, game_running=game_running)
    notify("Animatrix: %s" % type.capitalize() if type else "Disabled", config.get('notification_time'))
    if not type:
        return
    if type == "flash":
        animatrix_object = Flash(mc)
    elif type == "weather":
        weather_location = config.get("animatrix_weather", {}).get("location")
        weather_api_token = config.get("animatrix_weather", {}).get("api_token")
        weather_mountains = config.get("animatrix_weather", {}).get("mountains", True)
        weather_clock = config.get("animatrix_weather", {}).get("clock", True)
        weather_12_hour_time = config.get("animatrix_weather", {}).get("12_hour_time", True)
        weather_day_night_cycle = config.get("animatrix_weather", {}).get("day_cycle", True)
        animatrix_object = Weather(mc, weather_location, weather_api_token,
                                   mountains=weather_mountains,
                                   clock=weather_clock,
                                   is12HourTime=weather_12_hour_time,
                                   day_night_cycle=weather_day_night_cycle
                                   )
    animatrix_thread_start()


def create_menu():  # This will create the menu in the tray app
    global dpp_GUID, app_GUID, use_animatrix, animatrix_enabled, config, ac, status_menuItem, game_running, auto_power_switch
    status_menuItem = pystray.MenuItem("", None, default=True, enabled=False)
    status_menuItem._text = lambda _: "AC: %s Game: %s" % ("ON" if ac else "OFF", "ON" if game_running else "OFF")
    menu = pystray.Menu(
        status_menuItem,
        # The default setting will make the action run on left click
        pystray.MenuItem("CPU Boost", pystray.Menu(  # The "Boost" submenu
            pystray.MenuItem("Boost OFF", lambda: set_boost(config, user_settings, 0, dpp_GUID, app_GUID, plugged_in=ac,
                                                            game_running=game_running),
                             checked=lambda _: user_settings.get("boost", 0, plugged_in=ac,
                                                                 game_running=game_running) == 0),
            pystray.MenuItem("Boost Efficient Aggressive",
                             lambda: set_boost(config, user_settings, 4, dpp_GUID, app_GUID, plugged_in=ac,
                                               game_running=game_running),
                             checked=lambda _: user_settings.get("boost", 0, plugged_in=ac,
                                                                 game_running=game_running) == 4),
            pystray.MenuItem("Boost Aggressive",
                             lambda: set_boost(config, user_settings, 2, dpp_GUID, app_GUID, plugged_in=ac,
                                               game_running=game_running),
                             checked=lambda _: user_settings.get("boost", 0, plugged_in=ac,
                                                                 game_running=game_running) == 2),
        )),
        pystray.MenuItem("dGPU", pystray.Menu(
            pystray.MenuItem("dGPU ON",
                             lambda: set_dgpu(config, user_settings, True, plugged_in=ac, game_running=game_running),
                             checked=lambda _: get_dgpu()),
            pystray.MenuItem("dGPU OFF",
                             lambda: set_dgpu(config, user_settings, False, plugged_in=ac, game_running=game_running),
                             checked=lambda _: not get_dgpu()),
        )),
        pystray.MenuItem("Screen Refresh", pystray.Menu(
            pystray.MenuItem("120Hz",
                             lambda: set_screen(config, user_settings, 120, plugged_in=ac, game_running=game_running),
                             checked=lambda _: get_screen(config)),
            pystray.MenuItem("60Hz",
                             lambda: set_screen(config, user_settings, 60, plugged_in=ac, game_running=game_running),
                             checked=lambda _: not get_screen(config)),
        ), visible=check_screen(config)),
        pystray.MenuItem("CPU TDP", pystray.Menu(
            pystray.MenuItem("15 watts", lambda: set_ryzenadj(config, user_settings, 15000, plugged_in=ac,
                                                              game_running=game_running),
                             checked=lambda _: user_settings.get("cpu_tdp", 35000, plugged_in=ac,
                                                                 game_running=game_running) == 15000),
            pystray.MenuItem("25 watts", lambda: set_ryzenadj(config, user_settings, 25000, plugged_in=ac,
                                                              game_running=game_running),
                             checked=lambda _: user_settings.get("cpu_tdp", 35000, plugged_in=ac,
                                                                 game_running=game_running) == 25000),
            pystray.MenuItem("35 watts", lambda: set_ryzenadj(config, user_settings, 35000, plugged_in=ac,
                                                              game_running=game_running),
                             checked=lambda _: user_settings.get("cpu_tdp", 35000, plugged_in=ac,
                                                                 game_running=game_running) == 35000),
            pystray.MenuItem("45 watts", lambda: set_ryzenadj(config, user_settings, 45000, plugged_in=ac,
                                                              game_running=game_running),
                             checked=lambda _: user_settings.get("cpu_tdp", 35000, plugged_in=ac,
                                                                 game_running=game_running) == 45000),
            pystray.MenuItem("55 watts", lambda: set_ryzenadj(config, user_settings, 55000, plugged_in=ac,
                                                              game_running=game_running),
                             checked=lambda _: user_settings.get("cpu_tdp", 35000, plugged_in=ac,
                                                                 game_running=game_running) == 55000),
        )),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Windows Power Plan", pystray.Menu(
            pystray.MenuItem(config.get('default_power_plan'), lambda: set_power_plan(config, dpp_GUID)),
            pystray.MenuItem(config.get('alt_power_plan'), lambda: set_power_plan(config, app_GUID)),
        )),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Auto Power Switching", toggle_powerswitching, checked=lambda _: auto_power_switch),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Custom", None,
                         checked=lambda _: user_settings.get("name", "Custom", plugged_in=ac,
                                                             game_running=game_running) == "Custom",
                         enabled=False),
        # I have no idea of what I am doing, fo real, man.
        *list(map(
            (lambda plan: pystray.MenuItem(plan['name'], lambda: apply_plan(plan),
                                           checked=lambda _: plan["name"] == user_settings.get(
                                               "name", "Custom", plugged_in=ac, game_running=game_running))),
            config.get('plans'))),  # Blame @dedo1911 for this. You can find him on github.
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("AniMatrix", pystray.Menu(
            pystray.MenuItem("Disable", lambda: apply_animatrix(),
                             checked=lambda _: not user_settings.get("animatrix", "flash", plugged_in=ac,
                                                                     game_running=game_running)),
            pystray.MenuItem("Flash", lambda: apply_animatrix('flash'),
                             checked=lambda _: user_settings.get("animatrix", "flash", plugged_in=ac,
                                                                 game_running=game_running) == "flash"),
            pystray.MenuItem("Weather", lambda: apply_animatrix('weather'),
                             checked=lambda _: user_settings.get("animatrix", "flash", plugged_in=ac,
                                                                 game_running=game_running) == "weather"),
        ), visible=use_animatrix),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app)  # This to close the app, we will need it.
    )
    return menu


"""
def get_max_charge():
    global max_charge_key_loc, dpp_GUID, app_GUID
    maxChargeKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, max_charge_key_loc, 0, winreg.KEY_ALL_ACCESS)
    currMaxVal = winreg.QueryValueEx(maxChargeKey, "ChargingRate")[0]
    winreg.CloseKey(winreg.HKEY_LOCAL_MACHINE)
    return currMaxVal

def set_max_charge(maxval):
    global max_charge_key_loc
    try:
        if maxval < 20 or maxval > 100:
            return False
    except:
        return False
    
    maxChargeKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, max_charge_key_loc, 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(maxChargeKey, "ChargingRate", 1, winreg.REG_DWORD, maxval)
    set_power_plan(app_GUID)
    time.sleep(0.25)
    set_power_plan(dpp_GUID)
    return True
"""


def startup_checks():
    global auto_power_switch, registry_key_loc
    # Only enable auto_power_switch on boot if default power plans are enabled (not set to null):
    if config.get("default_ac_plan") is not None and config.get("default_dc_plan") is not None:
        auto_power_switch = True
    else:
        auto_power_switch = False
    # Adds registry entry if enabled in config, but not when in debug mode and if not registry entry is already existing, removes registry entry if registry exists but setting is disabled:
    if config.get('start_on_boot') and not config.get('debug') and not registry_check(registry_key_loc, get_G14_dir()):
        registry_add(registry_key_loc, get_G14_dir())
    if not config.get('start_on_boot') and not config.get('debug') and registry_check(registry_key_loc, get_G14_dir()):
        registry_remove(registry_key_loc, get_G14_dir())


def user_settings_updated(config):
    try:
        global icon_app
        icon_app.menu = create_menu()
    except:
        print("icon_app not defined yet")


if __name__ == "__main__":
    #
    frame = []
    config = Config(get_G14_dir())  # Make the config available to the whole script
    user_settings = UserSettings(get_G14_dir(), callback=user_settings_updated)
    dpp_GUID, app_GUID = get_power_plans()  # sets dpp_GUID and app_GUID
    use_animatrix = True
    game_running = False
    ac = False
    mc = MatrixController.MatrixController()
    try:
        use_animatrix = mc.connected
    except:
        use_animatrix = False
    if is_admin() or config.get('debug'):  # If running as admin or in debug mode, launch program
        plan_name = user_settings.get('name', config.get("default_starting_plan"), plugged_in=ac,
                                      game_running=game_running)
        # default_ac_plan = user_settings.get('ac_plan', config.get('default_ac_plan'), plugged_in=ac, game_running=game_running)
        # default_dc_plan = user_settings.get('dc_plan', config.get('default_dc_plan'), plugged_in=ac, game_running=game_running)
        plan = {}
        if plan_name == "Custom":
            plan = user_settings.get_plan(plugged_in=ac, game_running=game_running)
        else:
            plan = get_plan_by_name(plan_name)
        apply_plan(plan)
        print("apply plan from main_thread")
        # set_boost(config, current_boost_mode, dpp_GUID, app_GUID)
        registry_key_loc = r'Software\Microsoft\Windows\CurrentVersion\Run'
        # max_charge_key_loc = r'SOFTWARE\WOW6432Node\ASUS\ASUS Battery Health Charging'
        auto_power_switch = False  # Set variable before startup_checks decides what the value should be
        ac = psutil.sensors_battery().power_plugged  # Set AC/battery status on start
        resources.extract(config.get('temp_dir'))
        startup_checks()

        power_thread = Thread(target=power_check, daemon=True)
        power_thread.start()
        if config.get('default_gaming_plan') is not None and config.get('default_gaming_plan_games') is not None:
            gaming_thread = Thread(target=gaming_check, daemon=True)
            gaming_thread.start()
        if use_animatrix:
            apply_animatrix(user_settings.get("animatrix", plugged_in=ac, game_running=game_running))

        if config.get('rog_key') != None:
            filter = hid.HidDeviceFilter(vendor_id=0x0b05, product_id=0x1866)
            hid_device = filter.get_devices()
            for i in hid_device:
                if str(i).find("col01"):
                    device = i
                    device.open()
                    device.set_raw_data_handler(readData)

        default_gaming_plan_games = config.get('default_gaming_plan_games')
        icon_app = pystray.Icon(config.get('app_name'))  # Initialize the icon app and set its name
        icon_app.title = config.get('app_name')  # This is the displayed name when hovering on the icon
        icon_app.icon = create_icon()  # This will set the icon itself (the graphical icon)
        icon_app.menu = create_menu()  # This will create the menu
        icon_app.run()  # This runs the icon. Is single threaded, blocking.
    else:  # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
