import os
import sys
import requests
from dotenv import load_dotenv
from src.bot.exception import CustomException
from src.bot.logger import logging


def configure():
    load_dotenv()


def get_ip_address():
    try:
        configure()
        ip = requests.get(os.getenv('ip_api_key')).text
        logging.info("ip address collected successfully")
        return ip
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def get_location(ip):
    try:
        location = requests.get(f"https://ipapi.co/{ip}/city/").text
        logging.info("Location collected successfully")
        return location
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def get_weather(location):
    try:
        configure()
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={os.getenv('weather_api_key')}"
        response = requests.get(url).json()

        if response.get("cod") == 200:
            weather_desc = response["weather"][0]["main"].lower()
            logging.info(f"current weather condition is {weather_desc}")
            return weather_desc
        else:
            return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def weather_greeting(weather_desc):
    try:
        if weather_desc is None:
            return None

        if weather_desc in ["thunderstorm", "drizzle", "rain", "snow"]:
            return f"It seems like there's {weather_desc} outside. Stay safe!"
        elif weather_desc in ["atmosphere", "clear", "clouds"]:
            return f"Enjoy the {weather_desc} weather!"
        elif weather_desc in ["mist", "smoke", "haze", "dust", "fog", "sand", "ash"]:
            return f"Be cautious as there's {weather_desc} in the air."
        elif weather_desc in ["squall", "tornado"]:
            return f"Take extra precautions due to {weather_desc} in the area."
        else:
            return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

if __name__=="__main__":
    ip = get_ip_address()
    print(ip)
    ip_location = get_location(ip)
    print(ip_location)
    weather_desc = get_weather(ip_location)
    print(weather_desc)
    weather_info_greet = weather_greeting(weather_desc)
    print(weather_info_greet)
