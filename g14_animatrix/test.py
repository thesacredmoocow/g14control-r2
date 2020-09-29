# import MatrixController
#
# import time
# from g14_animatrix.weather_matrix import Weather
# from datetime import datetime, timedelta
# mc = MatrixController.MatrixController()
# weather = Weather(mc, "Hanmer Springs, nz", "<openweathermap api token>")
# frame_refresh_millis = 100
# while True:
#     currentTime = datetime.now()
#     weather.updateFrame()
#     render_time_millis = ((datetime.now() - currentTime).microseconds / 1000)
#     time.sleep(max((frame_refresh_millis - render_time_millis) / 1000, 0))
