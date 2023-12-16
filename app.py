import os
from flask import Flask, jsonify, request
import re
import requests
from datetime import datetime, timezone
import mysql.connector as conn
from src.logger import logging
from dotenv import load_dotenv


app = Flask(__name__)


def configure():
    load_dotenv()

configure()
host = os.getenv("database_host_name")
user_name = os.getenv("database_user_name")
password = os.getenv("database_user_password")
database = os.getenv("database_name")


# Connection from Python to MySQL
mydb = conn.connect(host=host,user=user_name,password=password,database=database)
cursor = mydb.cursor()

# Get current UTC date and time
current_utc_datetime = datetime.now(timezone.utc)

# Extract date and time separately
utc_date = current_utc_datetime.strftime('%Y-%m-%d')
utc_time = current_utc_datetime.strftime('%H:%M:%S')


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
    

# this API is responsible for choosing client type
@app.route("/chatbot/client", methods=["POST"])
def client():
    try:
        data = request.get_json()
        client_type = data.get("client_type")
        welcome_messages = {
            "1": "Welcome, New client!",
            "2": "Welcome, existing client!",
            "3": "Welcome, Job seeker!",
            "4": "Bye!",
        }
        if client_type not in welcome_messages:
            message = "Invalid option. Please choose a valid option."
            status_code = 400
        else:
            message = welcome_messages[client_type]
            status_code = 200

        logging.info(f"Client type found: {message}")
        return jsonify({"message": message, "code": status_code})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API responsible for collecting user details from new client and save in DB
@app.route("/chatbot/new_client_details", methods=["POST"])
def new_client_details():
    try:
        ip_address = get_ip_address()
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        contact = data.get("contact")
        company = data.get("company")

        if not is_valid_name(name):
            return jsonify({"message": "Please enter a valid name.", "code": 400})

        if not is_valid_email(email):
            return jsonify({"message": "Please enter a valid email address.", "code": 400})

        if not is_valid_contact_number(contact):
            return jsonify({"message": "Please enter a valid contact number.", "code": 400})

        user_details = {"ip_address":ip_address, "name": name, "email": email, "contact": contact, "company":company}

        query = "INSERT INTO new_client (DATE, TIME, IP_ADDRESS, NAME, EMAIL_ID, CONTACT_NUMBER, COMPANY_NAME) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (utc_date, utc_time, ip_address, name, email, contact, company, )
        cursor.execute(query, values)
        row_id = cursor.lastrowid  # Get the ID (primary key) of the inserted row
        mydb.commit()  # Commit the changes to the database
        logging.info("user details saved in database")
        return jsonify(
            {
                "message": "User details collected successfully.",
                "row_id": row_id,
                "code": 200,
            }
        )
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500


def is_valid_name(name):
    return bool(re.match(r"^[A-Za-z\s]+$", name.strip()))


def is_valid_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def is_valid_contact_number(contact):
    return bool(re.match(r"^\+?\d{1,3}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$",contact,))


# this API is responsible for selecting industries
@app.route("/chatbot/new_client/user_details/industries", methods=["POST"])
def industries():
    try:
        industries = {
            "1": "Insurance",
            "2": "Banking",
            "3": "Finance",
            "4": "IT",
            "5": "Healthcare",
            "6": "Internet",
            "7": "Automobile",
            "8": "Others",
        }
        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        selected_options = data.get("selected_options", [])
        selected_industries = [
            industries[opt] for opt in selected_options if opt in industries
        ]

        industry_str = ",".join(selected_industries)  # Convert lists to strings

        query = "UPDATE new_client SET INDUSTRY = %s WHERE ID = %s"
        values = (industry_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info("new client industry saved in DB - {industry_str}")
        return jsonify({"selected_industries": selected_industries, "code": 200})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API is responsible for selecting verticals
@app.route("/chatbot/new_client/user_details/industries/verticals", methods=["POST"])
def verticals_new_client():
    try:
        verticals = {
            "1": "ML/DS/AI",
            "2": "Sales force",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "Others",
        }

        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        selected_options = data.get("selected_options", [])
        selected_verticals = [verticals[opt] for opt in selected_options if opt in verticals]

        vertical_str = ",".join(selected_verticals)

        query = "UPDATE new_client SET VERTICAL = %s WHERE ID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info("new client vertical saved in DB - {vertical_str}")
        return jsonify({"selected_verticals": selected_verticals, "code": 200})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API is responsible for selecting requirements
@app.route("/chatbot/new_client/user_details/industries/verticals/requirement",methods=["POST"])
def requirement():
    try:
        requirements = {
            "1": "Start the project from scratch",
            "2": "Require support from existing project",
            "3": "Looking for some kind of solutions",
            "4": "Others",
        }

        data = request.get_json()
        selected_option = data.get("selected_option")
        row_id = data.get("row_id")  # Get the user ID from the request

        if selected_option in requirements:
            selected_requirement = requirements[selected_option]

            query = "UPDATE new_client SET REQUIREMENTS = %s WHERE ID = %s"
            values = (selected_requirement, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info("new client requirement saved in DB - {selected_requirement}")
            return jsonify({"selected_requirement": selected_requirement, "code": 200})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500





if __name__ == "__main__":
    app.run(debug=True)
