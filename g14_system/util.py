import ctypes
import os
import subprocess
import sys
import winreg

import yaml


def registry_check(registry_key_loc, G14dir):  # Checks if G14Control registry entry exists already
    G14exe = "G14Control.exe"
    G14fileloc = os.path.join(G14dir, G14exe)
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


def registry_remove(registry_key_loc, G14dir):  # Removes G14Control.exe from the windows registry
    G14exe = "G14Control.exe"
    G14fileloc = os.path.join(G14dir, G14exe)
    G14Key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key_loc, 0, winreg.KEY_ALL_ACCESS)
    winreg.DeleteValue(G14Key, 'G14Control')
    winreg.CloseKey(winreg.HKEY_LOCAL_MACHINE)


def registry_add(registry_key_loc, G14dir):  # Adds G14Control.exe to the windows registry to start on boot/login
    G14exe = "G14Control.exe"
    G14fileloc = os.path.join(G14dir, G14exe)
    G14Key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key_loc, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(G14Key, "G14Control", 1, winreg.REG_SZ, G14fileloc)
    winreg.CloseKey(winreg.HKEY_LOCAL_MACHINE)


def set_power_plan(config, GUID, notification_callback=None):
    global dpp_GUID, app_GUID
    subprocess.check_output(["powercfg", "/s", GUID])
    if notification_callback:
        if GUID == dpp_GUID:
            notification_callback("set power plan to " + config.get('default_power_plan'),
                                  config.get('notification_time'))
        elif GUID == app_GUID:
            notification_callback("set power plan to " + config.get('alt_power_plan'), config.get('notification_time'))


def get_G14_dir():
    if getattr(sys, 'frozen', False):  # Sets the path accordingly whether it is a python script or a frozen .exe
        return os.path.dirname(os.path.realpath(sys.executable))
    else:
        return os.getcwd()


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
    key = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)  # By default, this is the local registry
    sub_key = winreg.OpenKey(key,
                             "Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")  # Let's open the subkey
    value = winreg.QueryValueEx(sub_key, "SystemUsesLightTheme")[
        0]  # Taskbar (where icon is displayed) uses the 'System' light theme key. Index 0 is the value, index 1 is the type of key
    return value  # 1 for light theme, 0 for dark theme
