class Config:
    # Weather Undeground configuration
    STATION_ID = 'KCASANJO674'
    STATION_KEY = 'mfycfvvg'
    WU_URL = 'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'

    # Runtime configuration
    WEATHER_UPLOAD = True
    UPLOAD_INTERVAL = 10 #in seconds
    LOG_TO_CONSOLE = True
    LOG_INTERVAL = 5 #in seconds

    # Visual styles configuration
    TEMP_POSITIVE = (255, 0, 0)    # red
    TEMP_NEGATIVE = (0, 0, 255)    # blue
    HUM_POSITIVE = (0, 255, 0)     # green
    HUM_NEGATIVE = (255, 255, 255) # white
    PRESS_POSITIVE = (186,85,211)  # purple
    PRESS_NEGATIVE = (255,165,0)   # orange
    
