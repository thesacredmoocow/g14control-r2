import json
import time
from datetime import timedelta

import requests

from g14_animatrix.ani_frame import Frame
from g14_animatrix.base_animatrix import Animatrix
import math
import random
from g14_animatrix.matrix_object import *


class Weather(Animatrix):
    matrixObjects = {}

    def __init__(self, matrix_controller, location_string, openweathermap_token,
                 mountains=True,
                 clock=True,
                 is12HourTime=True,
                 day_night_cycle=True
                 ):
        super().__init__(matrix_controller)
        self.lastWeatherUpdate = datetime.fromtimestamp(0)
        self.location_string = location_string
        self.openweathermap_token = openweathermap_token
        if clock:
            self.matrixObjects["time"] = [Time.generate(is12HourTime=is12HourTime)]
        if day_night_cycle:
            self.matrixObjects["sun"] = [Sun.generate()]
            self.matrixObjects["moon"] = [Moon.generate()]
        if mountains:
            self.matrixObjects["mountains"] = [Mountains.generate()]

        self.matrixObjects["haze"] = [CloudHaze.generate()]
        self.matrixObjects["clouds"] = []

    def drawFrame(self, weather_config):
        frameMatrix = self.fullMatrix()
        if self.shouldAddCloud(weather_config):
            self.matrixObjects["clouds"].append(Cloud.generate(weather_config=weather_config))
        for objectCategory in self.matrixObjects:
            for matrixObject in self.matrixObjects[objectCategory]:
                if matrixObject.outOfBounds():
                    self.matrixObjects[objectCategory].remove(matrixObject)
                else:
                    frameMatrix = self.addObjectToMatrix(matrixObject, frameMatrix, weather_config)
                for child in matrixObject.getChildren():
                    frameMatrix = self.addObjectToMatrix(child, frameMatrix, weather_config)
        matrix = self.cropMatrix(frameMatrix)
        self.drawMatrix(matrix)

    def shouldAddCloud(self, weather_config):
        cloud_density = weather_config.get("cloudiness_percent", 0) / 10
        cloudsBelowDensity = len(self.matrixObjects["clouds"]) < cloud_density / 10
        cloudPositions = [cloud.xPos for cloud in self.matrixObjects["clouds"]]
        cloudPositions.append(Frame.fullWidth())
        lastCloudSpacedOutEnough = min(cloudPositions) > Frame.fullWidth() / max(cloud_density, 1)
        return cloudsBelowDensity and lastCloudSpacedOutEnough

    def addObjectToMatrix(self, matrixObject, matrix, weather_config):
        matrixObject.moveFrame(weather_config)  # update the frame first with the new data.
        data = matrixObject.getData()
        posX = matrixObject.xPos - (matrixObject.xPos % max(matrixObject.xStep, 1))
        posY = matrixObject.yPos - (matrixObject.yPos % max(matrixObject.yStep, 1))
        for indexY, row in enumerate(data):
            if row:
                for indexX, brightness in enumerate(row):
                    relativeX = indexX + posX
                    relativeY = indexY + posY
                    self.safe_add(matrix, math.floor(relativeX), math.floor(relativeY), brightness)
        return matrix

    def safe_assign(self, matrix, x, y, value):
        if y < len(matrix) and x < len(matrix[y]):
            matrix[y][x] = value

    def safe_add(self, matrix, x, y, value):
        if y < len(matrix) and x < len(matrix[y]):
            matrix[y][x] += value

    def cropMatrix(self, matrix):
        # 60x120 -> 33x54
        # top left     x:14 y:33
        # bottom right x:47 y:87

        new_matrix = []
        for i in range(7):
            new_matrix.append(matrix[33 + i][14:47])
        row = 0
        for i in range(24):
            new_matrix.append(matrix[40 + row][15 + i:47])
            new_matrix.append(matrix[40 + row + 1][15 + i:47])
            row += 2
        return new_matrix

    def fullMatrix(self):
        matrix = []
        for i in range(0, Frame.fullHeight()):
            matrix.append([0] * Frame.fullWidth())
        return matrix

    def emptyMatrix(self):
        matrix = []
        matrix.append([0] * 33)
        matrix.append([0] * 33)
        matrix.append([0] * 33)
        matrix.append([0] * 33)
        matrix.append([0] * 33)
        for i in range(0, 24, 2):
            matrix.append([0] * (33-i))
            matrix.append([0] * (33-i))
        return matrix

    def updateFrame(self):
        # DEFAULT CONFIG
        weather_config = {'sunrise': datetime(1970, 1, 1, 6, 0, 0), 'sunset': datetime(1970, 1, 1, 18, 0, 0),
                          'cloudiness_percent': 0.0, 'rain_1h_mm': 0.0, 'snow_1h_mm': 0.0, 'wind_speed_mps': 0.0}

        currentTime = datetime.now()
        if self.lastWeatherUpdate + timedelta(hours=1) < currentTime:
            try:
                response = requests.get(
                    "https://api.openweathermap.org/data/2.5/weather?q=%s&APPID=%s" % (
                        self.location_string, self.openweathermap_token))
                loads = json.loads(response.content)
                weather_config = {
                    "sunrise": datetime.fromtimestamp(
                        loads.get("sys").get("sunrise",
                                             currentTime.replace(hour=6, minute=0, second=0, microsecond=0))),
                    "sunset": datetime.fromtimestamp(
                        loads.get("sys").get("sunset",
                                             currentTime.replace(hour=18, minute=0, second=0, microsecond=0))),
                    "cloudiness_percent": loads.get("clouds", {}).get("all", 0),
                    "rain_1h_mm": loads.get("rain", {}).get("1h", 0),
                    "snow_1h_mm": loads.get("snow", {}).get("1h", 0),
                    "wind_speed_mps": loads.get("wind", {}).get("speed", 0),
                }
                print("Updated Weather: %s" % weather_config)
            except:
                print("Error updating weather")
            finally:
                self.lastWeatherUpdate = currentTime
        self.drawFrame(weather_config)
