
# Introduction  
This is a sensor suite for [Home Assistant](https://www.home-assistant.io/), which provides useful data related to air quality. It utilizes [Airly.eu](http://www.airly.eu) as the data provider.  
  
# Available sensors:  
| Sensor | Description |
|--|--|
| **CAQI** | Common Air Quality Index |
| **PM 1** | Atmospheric particulate matter less than 1 μm in size. Expressed in µg/m3. |
| **PM 2.5** | Atmospheric particulate matter less than 2.5 μm in size. Expressed in µg/m3. |
| **PM 10** | Atmospheric particulate matter less than 10 μm in size. Expressed in µg/m3.|
  
  
# CAQI  
What is CAQI?  
https://www.airqualitynow.eu/about_indices_definition.php  
  
# Installation  
Copy all files to `/config/custom_components/airly`.  
You might need to create `custom_components` and `airly` directories yourself.  
  
# Setup  
In your `configuration.yaml`:  
```
sensor:  
 - platform: airly 
   latitude: 52.212345
   longitude: 20.912345
   api_key: 'YOUR_API_KEY'
```  
  
# Api-Key  
Mandatory. Register at [Airly Developer](https://developer.airly.eu/login) to get one.
