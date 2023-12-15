import os
from flask import Flask, jsonify, request
import re
import requests
import mysql.connector as conn
from src.logger import logging
from dotenv import load_dotenv


app = Flask(__name__)


def configure():
    load_dotenv()


def get_ip_address():
    try:
        configure()
        ip = requests.get(os.getenv('ip_api_key')).text
        logging.info(f"ip address {ip} collected successfully")
        return ip
    except requests.RequestException as e:
        logging.error(f"Error getting IP address: {e}")
        print(f"Error getting IP address: {e}")
        return None


def get_location(ip):
    try:
        location = requests.get(f"https://ipapi.co/{ip}/city/").text
        logging.info(f"Location {location} collected successfully")
        return location
    except requests.RequestException as e:
        logging.error(f"Error getting location: {e}")
        print(f"Error getting location: {e}")
        return None


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
    except requests.RequestException as e:
        logging.error(f"Error getting weather: {e}")
        print(f"Error getting weather: {e}")
        return None


def weather_greeting(weather_desc):
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


# this API responsible for greeting the user
@app.route("/chatbot/greeting", methods=["GET"])
def get_greeting():
    try:
        ip = get_ip_address()
        ip_location = get_location(ip)
        weather_desc = get_weather(ip_location)
        weather_info_greet = weather_greeting(weather_desc)
        greeting = "Hello, buddy! Welcome to Datanetiix!"
        if ip_location and weather_info_greet:
            message = f"{greeting} We hope you're connecting from {ip_location}. {weather_info_greet}"
            logging.info(f"weather greet given to user - {message}")
            return jsonify({"status": "success", "message": message})
        else:
            message = greeting
            logging.info(f"weather greet given to user - {message}")
            return jsonify({"status": "success", "message": message})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
