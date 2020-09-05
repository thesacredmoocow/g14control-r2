from pystray import _win32
import pystray
from PIL import Image
import yaml
from winreg import *
import ctypes
import time
import os
import subprocess
import sys
import re
import psutil
import resources
import winreg
from threading import Thread
import MatrixController
import math
import random
import copy

class point:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.val = 0

showFlash = False

current_boost_mode = 0


newDotDelay = 80
threshold = 30
newDotCounter = 60
dotLength = 120
dot = point()
dots = []

def getDist(a, b):
    return math.sqrt((a.y - b.y) * (a.y - b.y) + (a.x - b.x) * (a.x - b.x))
    
def remap(source, ol, oh, nl, nh):
    orr = oh - ol
    nr = nh - nl;
    rat = nr / orr;
    return int((source - ol) * rat + nl)

def get_power_plans():
    global dpp_GUID, app_GUID
    all_plans = subprocess.check_output(["powercfg", "/l"])
    for i in str(all_plans).split('\\n'):
        if i.find(config['default_power_plan']) != -1:
            dpp_GUID = i.split(' ')[3]
        if i.find(config['alt_power_plan']) != -1:
            app_GUID = i.split(' ')[3]

def set_power_plan(GUID):
    #print("setting power plan GUID to: ", GUID)
    subprocess.check_output(["powercfg", "/s", GUID])

def get_app_path():
    global G14dir
    
    if getattr(sys, 'frozen', False):   # Sets the path accordingly whether it is a python script or a frozen .exe
        G14dir = os.path.dirname(os.path.realpath(sys.executable))
    elif __file__:
        G14dir = os.path.dirname(os.path.realpath(__file__))
def parse_boolean(parse_string):  # Small utility to convert windows HEX format to a boolean.
    try:
        if parse_string == "0x00000000":  # We will consider this as False
            return False
        else:  # We will consider this as True
            return True
    except Exception:
        return None  # Just in case™


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()  # Returns true if the user launched the app as admin
    except Exception:
        return False


def get_windows_theme():
    key = ConnectRegistry(None, HKEY_CURRENT_USER)  # By default, this is the local registry
    sub_key = OpenKey(key, "Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")  # Let's open the subkey
    value = QueryValueEx(sub_key, "SystemUsesLightTheme")[0]  # Taskbar (where icon is displayed) uses the 'System' light theme key. Index 0 is the value, index 1 is the type of key
    return value  # 1 for light theme, 0 for dark theme


def create_icon():
    if get_windows_theme() == 0:  # We will create the icon based on current windows theme
        return Image.open(os.path.join(config['temp_dir'], 'icon_light.png'))
    else:
        return Image.open(os.path.join(config['temp_dir'], 'icon_dark.png'))


def power_check():
    global auto_power_switch, ac, current_plan, default_ac_plan, default_dc_plan
    if auto_power_switch:     # Only run while loop on startup if auto_power_switch is On (True)
        while True:
            if auto_power_switch:   # Check to user hasn't disabled auto_power_switch (i.e. by manually switching plans)
                ac = psutil.sensors_battery().power_plugged     # Get the current AC power status
                if ac and current_plan != default_ac_plan:      # If on AC power, and not on the default_ac_plan, switch to that plan
                    for plan in config['plans']:
                        if plan['name'] == default_ac_plan:
                            break
                    apply_plan(plan)
                if not ac and current_plan != default_dc_plan:      # If on DC power, and not on the default_dc_plan, switch to that plan
                    for plan in config['plans']:
                        if plan['name'] == default_dc_plan:
                            break
                    apply_plan(plan)
            time.sleep(10)
    else:
        return


def activate_powerswitching():
    global auto_power_switch
    auto_power_switch = True
    #time.sleep(10)   # Plan change notifies first, so this needs to be on a delay to prevent simultaneous notifications
    #notify("Auto power switching has been ENABLED")


def deactivate_powerswitching():
    global auto_power_switch
    auto_power_switch = False
    #time.sleep(10)   # Plan change notifies first, so this needs to be on a delay to prevent simultaneous notifications
    #notify("Auto power switching has been DISABLED")


def gaming_check():     # Checks if user specified games/programs are running, and switches to user defined plan, then switches back once closed
    global  _plan, default_gaming_plan_games
    previous_plan = None    # Define the previous plan to switch back to

    while True: # Continuously check every 10 seconds
        output = os.popen('wmic process get description, processid').read() 
        process = output.split("\n")
        processes = set(i.split(" ")[0] for i in process)
        targets = set(default_gaming_plan_games)    # List of user defined processes
        if processes & targets:     # Compare 2 lists, if ANY overlap, set game_running to true
            game_running = True
        else:
            game_running = False
        if game_running and current_plan != default_gaming_plan:    # If game is running and not on the desired gaming plan, switch to that plan
            previous_plan = current_plan
            for plan in config['plans']:
                if plan['name'] == default_gaming_plan:
                    break
            apply_plan(plan)
            notify(plan['name'])
        if not game_running and previous_plan is not None and previous_plan != current_plan:    # If game is no longer running, and not on previous plan already (if set), then switch back to previous plan
            for plan in config['plans']:
                if plan['name'] == previous_plan:
                    break
            apply_plan(plan)
        time.sleep(10)      # Check for programs every 10 sec


def notify(message):
    Thread(target=do_notify, args=(message,), daemon=True).start()


def do_notify(message):
    global icon_app
    icon_app.notify(message)  # Display the provided argument as message
    time.sleep(config['notification_time'])  # The message is displayed for the configured time. This is blocking.
    icon_app.remove_notification()  # Then, we will remove the notification

#(["Disabled", "Enabled", "Aggressive", "Efficient Enabled", "Efficient Aggressive"][int(get_boost()[2:])])
def get_current():
    global ac, current_plan, current_boost_mode
    notify(
        "Plan: " + current_plan + "     dGPU: " + (["Off", "On"][get_dgpu()]) + "\n" +
        "Boost: " + (["Disabled", "Enabled", "Aggressive", "Efficient Enabled", "Efficient Aggressive"][int(get_boost()[2:])]) + "\n" +
        "Refresh Rate: " + (["60Hz", "120Hz"][get_screen()]) + "\n" +
        "Power: " + (["Battery", "AC"][bool(ac)]) + "     Auto Switching: " + (["Off", "On"][auto_power_switch]) + "\n"
        #"Boost mode: " + str(current_boost_mode) + "\n" (["Disabled", "Enabled", "Aggressive", "Efficient Enabled", "Efficient Aggressive"][int(current_boost_mode)])
    )  # Let's print the current values


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


def set_boost(state, notification=True):
    global current_boost_mode
    current_boost_mode = state
    #print(state)
    global dpp_GUID, app_GUID
    #print("GUID ", dpp_GUID)
    set_power_plan(dpp_GUID)
    current_pwr = os.popen("powercfg /GETACTIVESCHEME")  # Just to be safe, let's get the current power scheme
    pwr_guid = current_pwr.readlines()[0].rsplit(": ")[1].rsplit(" (")[0].lstrip("\n")  # Parse the GUID
    if state is True:  # Activate boost
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        if notification is True:
            notify("Boost ENABLED")  # Inform the user
    elif state is False:  # Deactivate boost
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        if notification is True:
            notify("Boost DISABLED")  # Inform the user
    elif state == 0:
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0"
        )
        if notification is True:
            notify("Boost DISABLED")  # Inform the user
    elif state == 4:
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 4"
        )
        if notification is True:
            notify("Boost set to Efficient Aggressive")  # Inform the user
    elif state == 2:
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2"
        )
        if notification is True:
            notify("Boost set to Aggressive")  # Inform the user
    set_power_plan(app_GUID)
    time.sleep(0.25)
    set_power_plan(dpp_GUID)


def get_dgpu():
    current_pwr = os.popen("powercfg /GETACTIVESCHEME")  # I know, it's ugly, but no other way to do that from py.
    pwr_guid = current_pwr.readlines()[0].rsplit(": ")[1].rsplit(" (")[0].lstrip("\n")  # Parse the GUID
    pwr_settings = os.popen(
        "powercfg /Q " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857"
    )  # Let's get the dGPU status in the current power scheme
    output = pwr_settings.readlines()  # We save the output to parse it afterwards
    dgpu_ac = parse_boolean(output[-3].rsplit(": ")[1].strip("\n"))  # Convert to boolean for "On/Off"
    return dgpu_ac


def set_dgpu(state, notification=True):
    global G14dir
    current_pwr = os.popen("powercfg /GETACTIVESCHEME")  # Just to be safe, let's get the current power scheme
    pwr_guid = current_pwr.readlines()[0].rsplit(": ")[1].rsplit(" (")[0].lstrip("\n")  # Parse the GUID
    if state is True:  # Activate dGPU
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 2"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 2"
        )
        if notification is True:
            notify("dGPU ENABLED")  # Inform the user
    elif state is False:  # Deactivate dGPU
        os.popen(
            "powercfg /setacvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 0"
        )
        os.popen(
            "powercfg /setdcvalueindex " + pwr_guid + " e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 0"
        )
        os.system("\"" + G14dir+"\\restartGPUcmd.bat" + "\"")
        if notification is True:
            notify("dGPU DISABLED")  # Inform the user



def check_screen():  # Checks to see if the G14 has a 120Hz capable screen or not
    checkscreenref = str(os.path.join(config['temp_dir'] + 'ChangeScreenResolution.exe'))
    screen = os.popen(checkscreenref + " /m /d=0")  # /m lists all possible resolutions & refresh rates
    output = screen.readlines()
    for line in output:
        if re.search("@120Hz", line):
            return True
    else:
        return False


def get_screen():  # Gets the current screen resolution
    getscreenref = str(os.path.join(config['temp_dir'] + 'ChangeScreenResolution.exe'))
    screen = os.popen(getscreenref + " /l /d=0")  # /l lists current resolution & refresh rate
    output = screen.readlines()
    for line in output:
        if re.search("@120Hz", line):
            return True
    else:
        return False


def set_screen(refresh, notification=True):
    if check_screen():  # Before trying to change resolution, check that G14 is capable of 120Hz resolution
        if refresh is None:
            set_screen(120)  # If screen refresh rate is null (not set), set to default refresh rate of 120Hz
        checkscreenref = str(os.path.join(config['temp_dir'] + 'ChangeScreenResolution.exe'))
        os.popen(
            checkscreenref + " /d=0 /f=" + str(refresh)
        )
        if notification is True:
            notify("Screen refresh rate set to: " + str(refresh) + "Hz")
    else:
        return


def set_atrofac(asus_plan, cpu_curve=None, gpu_curve=None):
    atrofac = str(os.path.join(config['temp_dir'] + "atrofac-cli.exe"))
    if cpu_curve is not None and gpu_curve is not None:
        os.popen(
            atrofac + " fan --cpu " + cpu_curve + " --gpu " + gpu_curve + " --plan " + asus_plan
        )
    elif cpu_curve is not None and gpu_curve is None:
        os.popen(
            atrofac + " fan --cpu " + cpu_curve + " --plan " + asus_plan
        )
    elif cpu_curve is None and gpu_curve is not None:
        os.popen(
            atrofac + " fan --gpu " + gpu_curve + " --plan " + asus_plan
        )
    else:
        os.popen(
            atrofac + " plan " + asus_plan
        )


def set_ryzenadj(tdp):
    ryzenadj = str(os.path.join(config['temp_dir'] + "ryzenadj.exe"))
    if tdp is None:
        pass
    else:
        os.popen(
            ryzenadj + " -a " + str(tdp) + " -b " + str(tdp)
        )


def apply_plan(plan):
    global current_plan
    current_plan = plan['name']
    set_atrofac(plan['plan'], plan['cpu_curve'], plan['gpu_curve'])
    set_boost(plan['boost'], False)
    set_dgpu(plan['dgpu_enabled'], False)
    set_screen(plan['screen_hz'], False)
    set_ryzenadj(plan['cpu_tdp'])
    notify("Applied plan " + plan['name'])
    


def quit_app():
    global mc
    if config["use_animatrix"]:
        mc.clearMatrix()
    icon_app.stop()  # This will destroy the the tray icon gracefully.

def flash_animatrix():
    global showFlash
    global inputMatrix
    global frame
    global newDotDelay
    global threshold
    global newDotCounter
    global dotLength
    global dot
    global dots
    global mc
    while(True):
        if showFlash:
            for i in range(len(mc.rowWidths)):
                for j in range(mc.rowWidths[i]):
                    frame[i][j].val = 0
            if newDotCounter >= newDotDelay:
                newDotCounter = 0
                newDot = point()
                newDot.y = random.randint(0, 54)
                newDot.x = random.randint(0, mc.rowWidths[newDot.y]-1)
                newDot.val = 0;
                newDot = frame[newDot.y][newDot.x];
                dots.append(copy.deepcopy(newDot));
            else:
                newDotCounter += 4
            for i in range(len(dots)):
                if dots[i].val >= dotLength:
                    del dots[i]
                    break
                else:
                    dots[i].val += 4

            for i in range(len(mc.rowWidths)):
                for j in range(mc.rowWidths[i]):
                    for k in range(len(dots)):
                        #print(dots[k].x, " ", dots[k].y)
                        if abs(getDist(dots[k], frame[i][j]) - dots[k].val * 1.5) < 20:
                            frame[i][j].val = remap(20 - abs(getDist(dots[k], frame[i][j]) - dots[k].val * 1.5), 0, 20, 0, min(dots[k].val*10, max(0, 255 -  dots[k].val*3.5)))
                        elif dots[k].val > 60 and abs(getDist(dots[k], frame[i][j]) - (dots[k].val - 60) * 1.5) < 20:
                            frame[i][j].val = remap(20 - abs(getDist(dots[k], frame[i][j]) - (dots[k].val - 60) * 1.5), 0, 20, 0, min(dots[k].val*10, max(0, 255 - (dots[k].val - 45) * 4)))
            for i in range(len(mc.rowWidths)):
                for j in range(mc.rowWidths[i]):
                    inputMatrix[i][j] = int(frame[i][j].val)
            mc.drawMatrix(inputMatrix);
        else:
            time.sleep(5)
            mc.clearMatrix()

def enable_animatrix():
    global showFlash
    notify("Animatrix Enabled")
    showFlash = True

def disable_animatrix():
    global showFlash
    notify("Animatrix Disabled")
    showFlash = False

def play_snake():
    global mc
    global showFlash
    prev_flash_state = showFlash
    showFlash = False
    mc.playSnake()
    showFlash - prev_flash_state

def create_menu():  # This will create the menu in the tray app
    global dpp_GUID, app_GUID
    menu = pystray.Menu(
        pystray.MenuItem("Current Config", get_current, default=True),  # The default setting will make the action run on left click
        pystray.MenuItem("CPU Boost", pystray.Menu(  # The "Boost" submenu
            pystray.MenuItem("Boost OFF", lambda: set_boost(0)),
            pystray.MenuItem("Boost Efficient Aggressive", lambda: set_boost(4)),
            pystray.MenuItem("Boost Aggressive", lambda: set_boost(2)),
        )),
        pystray.MenuItem("dGPU", pystray.Menu(
            pystray.MenuItem("dGPU ON", lambda: set_dgpu(True)),
            pystray.MenuItem("dGPU OFF", lambda: set_dgpu(False)),
        )),
        pystray.MenuItem("Screen Refresh", pystray.Menu(
            pystray.MenuItem("120Hz", lambda: set_screen(120)),
            pystray.MenuItem("60Hz", lambda: set_screen(60)),
        ), visible=check_screen()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Windows Power Plan", pystray.Menu(
            pystray.MenuItem(config['default_power_plan'], lambda: set_power_plan(dpp_GUID)),
            pystray.MenuItem(config['alt_power_plan'], lambda: set_power_plan(app_GUID)),
        )),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Disable Auto Power Switching", deactivate_powerswitching),
        pystray.MenuItem("Enable Auto Power Switching", activate_powerswitching),
        pystray.Menu.SEPARATOR,
        # I have no idea of what I am doing, fo real, man.
        *list(map((lambda plan: pystray.MenuItem(plan['name'], (lambda: (apply_plan(plan),deactivate_powerswitching())))), config['plans'])),  # Blame @dedo1911 for this. You can find him on github.
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Enable AniMatrix", enable_animatrix, visible=config["use_animatrix"]),
        pystray.MenuItem("Disable AniMatrix", disable_animatrix, visible=config["use_animatrix"]),
        pystray.MenuItem("Play Snake", play_snake, visible=config["use_animatrix"]),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app)  # This to close the app, we will need it.
    )
    return menu


def load_config():  # Small function to load the config and return it after parsing
    global G14dir
    if getattr(sys, 'frozen', False):   # Sets the path accordingly whether it is a python script or a frozen .exe
        config_loc = os.path.join(G14dir,"config.yml")      # Set absolute path for config.yaml
    elif __file__:
        config_loc = os.path.join(G14dir,"data\config.yml")      # Set absolute path for config.yaml
    
    with open(config_loc, 'r') as config_file:
        return yaml.load(config_file, Loader=yaml.FullLoader)


def registry_check():     # Checks if G14Control registry entry exists already
    global registry_key_loc, G14dir
    G14exe = "G14Control.exe"
    G14fileloc = os.path.join(G14dir,G14exe)
    G14Key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key_loc)
    try:
        i = 0
        while 1:
            name, value, type = winreg.EnumValue(G14Key, i)
            if name == "G14Control" and value == G14fileloc:
                return True
            i += 1
    except WindowsError:
        return False


def registry_add():     # Adds G14Control.exe to the windows registry to start on boot/login
    global registry_key_loc, G14dir
    G14exe = "G14Control.exe"
    G14fileloc = os.path.join(G14dir,G14exe)
    G14Key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key_loc, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(G14Key, "G14Control", 1, winreg.REG_SZ, G14fileloc)


def registry_remove():     # Removes G14Control.exe from the windows registry
    global registry_key_loc, G14dir
    G14exe = "G14Control.exe"
    G14fileloc = os.path.join(G14dir,G14exe)
    G14Key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key_loc, 0, winreg.KEY_ALL_ACCESS)
    winreg.DeleteValue(G14Key,'G14Control')





def startup_checks():
    global default_ac_plan, auto_power_switch
    # Only enable auto_power_switch on boot if default power plans are enabled (not set to null):
    if default_ac_plan is not None and default_dc_plan is not None:
        auto_power_switch = True
    else:
        auto_power_switch = False
    # Adds registry entry if enabled in config, but not when in debug mode and if not registry entry is already existing, removes registry entry if registry exists but setting is disabled:
    if config['start_on_boot'] and not config['debug'] and not registry_check():
        registry_add()
    if not config['start_on_boot'] and not config['debug'] and registry_check():
        registry_remove()


if __name__ == "__main__":
    frame = []
    G14dir = None
    get_app_path()
    config = load_config()  # Make the config available to the whole script
    dpp_GUID = None
    app_GUID = None
    get_power_plans()
    if(config['use_animatrix']):
        mc = MatrixController.MatrixController()
        inputMatrix = []
        for i in range(len(mc.rowWidths)):
            inputMatrix.append([0xff]*mc.rowWidths[i])
        for i in range(len(mc.rowWidths)):
            y = 66 + i * 11
            temp = []
            for j in range(mc.rowWidths[i]):
                x = 1080 - (45 + j * 30 + (i % 2) * 15)
                t = point()
                t.x = x;
                t.y = y;
                t.val = 0;
                temp.append(copy.deepcopy(t))
            frame.append(copy.deepcopy(temp))
    if is_admin() or config['debug']:  # If running as admin or in debug mode, launch program
        #global dpp_GUID, app_GUID
        #print("dpp_GUID: ", dpp_GUID)
        current_plan = config['default_starting_plan']
        default_ac_plan = config['default_ac_plan']
        default_dc_plan = config['default_dc_plan']
        registry_key_loc = r'Software\Microsoft\Windows\CurrentVersion\Run'
        auto_power_switch = False   # Set variable before startup_checks decides what the value should be
        ac = psutil.sensors_battery().power_plugged  # Set AC/battery status on start
        resources.extract(config['temp_dir'])
        startup_checks()
        Thread(target=power_check, daemon=True).start()  # A process in the background will check for AC, autoswitch plan if enabled and detected
        if(config['use_animatrix']):
            Thread(target=flash_animatrix, daemon=True).start()
        if(config['default_gaming_plan'] != None and config['default_gaming_plan_games'] != None):
            #print(config['default_gaming_plan'], config['default_gaming_plan_games'])
            Thread(target=gaming_check, daemon=True).start()
        default_gaming_plan = config['default_gaming_plan']
        default_gaming_plan_games = config['default_gaming_plan_games']
        icon_app = pystray.Icon(config['app_name'])  # Initialize the icon app and set its name
        icon_app.title = config['app_name']  # This is the displayed name when hovering on the icon
        icon_app.icon = create_icon()  # This will set the icon itself (the graphical icon)
        icon_app.menu = create_menu()  # This will create the menu
        icon_app.run()  # This runs the icon. Is single threaded, blocking.
    else:  # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
