# from threading import Thread
# import MatrixController
#
# from reprint import output
# import time
# from g14_animatrix.weather_matrix import Weather
# from g14_animatrix.ani_frame import Frame
# import requests
# import json
# from datetime import datetime, timedelta
# mc = MatrixController.MatrixController()
# weather = Weather(mc, "Hanmer Springs, nz", "313e9c430c0302da609941017b4fca5f")
# weatherThread = Thread(target=weather.run(), daemon=True)
# weatherThread.start()
import os
import sys

from g14_system.config import Config

def get_app_path():
    if getattr(sys, 'frozen', False):  # Sets the path accordingly whether it is a python script or a frozen .exe
        return os.path.dirname(os.path.realpath(sys.executable))
    elif __file__:
        return os.path.dirname(os.path.realpath(__file__))

cfg = Config("C:\\Users\\Idzuna\\Desktop\\test")
cfg.load_config()
cfg.config["animatrix"] = "weather"
cfg.update_config()
print("hi")