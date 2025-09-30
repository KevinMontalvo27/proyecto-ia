import openmeteo_requests
import pandas as pd
import certifi
import requests

# Crear cliente de Open-Meteo sin cache
openmeteo = openmeteo_requests.Client(session=requests.Session())

# Parámetros de la API
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 25.793,
    "longitude": -108.9981,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "rain",
        "precipitation_probability",
        "precipitation",
        "showers"
    ],
}

# Llamada a la API usando certificados de certifi
responses = openmeteo.weather_api(url, params=params, verify=certifi.where())

# Procesar la primera respuesta
response = responses[0]

#Info general
latitude = response.Latitude()
longitude = response.Longitude()
elevation = response.Elevation()
utc_offset = response.UtcOffsetSeconds()

#Datos por hora
hourly = response.Hourly()

temperature_2m = hourly.Variables(0).ValuesAsNumpy()
relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
rain = hourly.Variables(2).ValuesAsNumpy()
precipitation_probability = hourly.Variables(3).ValuesAsNumpy()
precipitation = hourly.Variables(4).ValuesAsNumpy()
showers = hourly.Variables(5).ValuesAsNumpy()

#Rango de fechas
dates = pd.date_range(
    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
    freq=pd.Timedelta(seconds=hourly.Interval()),
    inclusive="left"
)


print("Lat:", latitude)
print("Lon:", longitude)
print("Altura:", elevation)
print("Primeras 5 temperaturas:", temperature_2m[:5])
print("Primeras 5 humedades:", relative_humidity_2m[:5])
print("Probabilidad de precipitación (primeros 5):", precipitation_probability[:5])
