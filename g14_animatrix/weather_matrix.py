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
    weather_config = {
        "sunrise": datetime.now().replace(hour=6, minute=0, second=0, microsecond=0),
        "sunset": datetime.now().replace(hour=18, minute=0, second=0, microsecond=0),
        "wind": 0,
        "rain": 0,
        "snow": 0,
        "cloud": 0,
    }
    weather_override = False

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
        # testCloud = Cloud.generate()
        # testCloud.data = testCloud.small_cloud
        # testCloud.xPos = 30
        # testCloud.yPos = 35
        self.matrixObjects["clouds"] = [
            # testCloud
        ]

    def drawFrame(self, weather_config):
        frameMatrix = self.fullMatrix()
        if self.shouldAddCloud(weather_config):
            self.matrixObjects["clouds"].append(Cloud.generate())
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
        # cloud_density = weather_config.get("cloud", 0) / 10
        # cloudsBelowDensity = len(self.matrixObjects["clouds"]) < cloud_density / 10
        cloudPositions = [cloud.xPos for cloud in self.matrixObjects["clouds"]]
        cloudPositions.append(Frame.fullWidth())
        lastCloudSpacedOutEnough = min(cloudPositions) > Frame.fullWidth() / 8
        return weather_config.get("cloud", 0) == 1 and lastCloudSpacedOutEnough

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
            matrix.append([0] * (33 - i))
            matrix.append([0] * (33 - i))
        return matrix

    def updateWeather(self, openweathermapJson):
        currentTime = datetime.now()
        self.weather_config = {
            "sunrise": datetime.fromtimestamp(
                openweathermapJson.get("sys").get("sunrise",
                                                  currentTime.replace(hour=6, minute=0, second=0, microsecond=0))),
            "sunset": datetime.fromtimestamp(
                openweathermapJson.get("sys").get("sunset",
                                                  currentTime.replace(hour=18, minute=0, second=0, microsecond=0))),
            "wind": 0,
            "rain": 0,
            "snow": 0,
            "cloud": 0,
        }
        # 6-11 	Light Breeze
        # 20-28 	Moderate Breeze
        # 39-49 	Strong gale
        wind_speed = openweathermapJson.get("wind", {}).get("speed", 0) * 36  # km/h
        if wind_speed > 5:
            self.weather_config["wind"] = 1
        elif wind_speed > 20:
            self.weather_config["wind"] = 2
        elif wind_speed > 40:
            self.weather_config["wind"] = 3

        # Slight rain: Less than 0.5 mm per hour.
        # Moderate rain: Greater than 0.5 mm per hour, but less than 4.0 mm per hour.
        # Heavy rain: Greater than 4 mm per hour, but less than 8 mm per hour.
        rain_mm = openweathermapJson.get("rain", {}).get("1h", 0.0)
        if rain_mm > 0.0:
            self.weather_config["rain"] = 1
        elif rain_mm > 0.5:
            self.weather_config["rain"] = 2
        elif rain_mm > 4.0:
            self.weather_config["rain"] = 3

        snow_mm = openweathermapJson.get("snow", {}).get("1h", 0)
        if snow_mm > 0.0:
            self.weather_config["snow"] = 1
        elif snow_mm > 0.5:
            self.weather_config["snow"] = 2
        elif snow_mm > 4.0:
            self.weather_config["snow"] = 3

        cloud_percent = openweathermapJson.get("clouds", {}).get("all", 0)
        if cloud_percent > 0.0:
            self.weather_config["cloud"] = 1
        elif cloud_percent > 33.0:
            self.weather_config["cloud"] = 2
        elif cloud_percent > 66.0:
            self.weather_config["cloud"] = 3

    def updateFrame(self):
        currentTime = datetime.now()
        if not self.weather_override and self.lastWeatherUpdate + timedelta(minutes=10) < currentTime:
            try:
                response = requests.get("https://api.openweathermap.org/data/2.5/weather?q=%s&APPID=%s" % (
                    self.location_string, self.openweathermap_token))
                jsonResponse = json.loads(response.content)
                self.updateWeather(jsonResponse)
                print("Updated Weather: %s" % self.weather_config)
                # print("Raw: %s" % jsonResponse)
            except:
                print("Error updating weather")
            finally:
                self.lastWeatherUpdate = currentTime
        self.drawFrame(self.weather_config)
