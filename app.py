import os
from flask import Flask, jsonify, request
import re
import requests
from src.alert import send_email
from src.database import extract_new_client_details
from src.database import extract_existing_client_details
from src.database import extract_job_seeker_details
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
        logging.info(f"new client industry saved in DB - {industry_str}")
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
        logging.info(f"new client vertical saved in DB - {vertical_str}")
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
            logging.info(f"new client requirement saved in DB - {selected_requirement}")
            return jsonify({"selected_requirement": selected_requirement, "code": 200})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API is responsible for selecting known sources
@app.route("/chatbot/new_client/user_details/industries/verticals/requirement/known_source",methods=["POST"])
def known_source():
    try:
        known_sources = {
            "1": "Google",
            "2": "LinkedIn",
            "3": "Email Campaign",
            "4": "News Letter",
            "5": "Known resources",
            "6": "Others",
        }

        data = request.get_json()
        selected_option = data.get("selected_option")
        row_id = data.get("row_id")  # Get the user ID from the request

        if selected_option in known_sources:
            if selected_option in ["5", "6"]:
                source_specification = request.get_json().get("source_specification")
                selected_known_source = (known_sources[selected_option] + " : " + source_specification)
            else:
                selected_known_source = known_sources[selected_option]

            query = "UPDATE new_client SET KNOWN_SOURCE = %s WHERE ID = %s"
            values = (selected_known_source, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"new client known source saved in DB - {selected_known_source}")
            # extract new client details
            new_client_details = extract_new_client_details()
            logging.info("new client details extracted")
            ## Send email with the new client details
            if new_client_details:
                sender_email = os.getenv("sender_email")
                receiver_emails = os.getenv("receiver_emails").split(",")  # Convert comma-separated string to a list
                cc_email = os.getenv("cc_email")
                subject = "Datanetiix chatbot project Email alert testing demo"
                email_message = (
                    f"Hi, new user logged in our chatbot, Find the below details for your reference:\n\n"
                    f"New client details:\n\n"
                    f"Date: {new_client_details['date']}\n"
                    f"Time: {new_client_details['time']}\n"
                    f"IP: {new_client_details['ip_address']}\n"
                    f"Name: {new_client_details['name']}\n"
                    f"Email: {new_client_details['email']}\n"
                    f"Contact: {new_client_details['contact']}\n"
                    f"Company: {new_client_details['company']}\n"
                    f"Industries: {new_client_details['industries_choosen']}\n"
                    f"Verticals: {new_client_details['verticals_choosen']}\n"
                    f"Requirements: {new_client_details['requirement']}\n"
                    f"Known Source: {new_client_details['known_source']}"
                )
                send_email(sender_email,receiver_emails, cc_email, subject, email_message)
                #logging.info("mail sent successfully")
            # Close the cursor and connection
            cursor.close()
            mydb.close()
            logging.info("mail sent successfully")
            return jsonify({"selected_known_source": selected_known_source, "code": 200})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API responsible for collecting user details
@app.route("/chatbot/existing_client_details", methods=["POST"])
def existing_client_details():
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

        user_details = {"ip_address":ip_address, "name": name, "email": email, "contact": contact, "company": company}

        query = "INSERT INTO existing_client (DATE, TIME, IP_ADDRESS, NAME, EMAIL_ID, CONTACT_NUMBER, COMPANY_NAME) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (utc_date, utc_time, ip_address, name, email, contact, company)
        cursor.execute(query, values)
        row_id = cursor.lastrowid  # Get the ID (primary key) of the inserted row
        mydb.commit()  # Commit the changes to the database
        logging.info("existing client user details save in DB")
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
    return bool(re.match(r"^\+?\d{1,3}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$",contact))



# this API is responsible for selecting verticals for existing client and save in DB
@app.route("/chatbot/existing_client_details/verticals", methods=["POST"])
def verticals_exixting_client():
    try:
        verticals = {
            "1": "ML/DS/AI",
            "2": "Sales force",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "Others",
        }

        data = request.get_json()
        row_id = data.get("row_id")

        selected_options = data.get("selected_options", [])
        selected_verticals = [
            verticals[opt] for opt in selected_options if opt in verticals
        ]

        vertical_str = ",".join(selected_verticals)

        query = "UPDATE existing_client SET VERTICAL = %s WHERE ID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"existing client vertical selected - {vertical_str}")
        return jsonify({"selected_verticals": selected_verticals, "code": 200})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API is responsible for selecting issue_escalation for existing client and save in DB
@app.route("/chatbot/existing_client_details/verticals/issue_escalation", methods=["POST"])
def issue_escalation():
    try:
        issue_escalation_options = {
            "1": "Team Lead",
            "2": "Sales Person",
            "3": "Escalate Issue",
        }

        data = request.get_json()
        row_id = data.get("row_id")

        selected_option = data.get("selected_option")
        if selected_option in issue_escalation_options:
            selected_issue_escalation = issue_escalation_options[selected_option]

            query = "UPDATE existing_client SET ISSUE_ESCALATION = %s WHERE ID = %s"
            values = (selected_issue_escalation, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"issue escalation selected - {selected_issue_escalation}")
            return jsonify(
                {"selected_isse_type": selected_issue_escalation, "code": 200}
            )
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API is responsible for selecting issue_type for existing client and save in DB
@app.route("/chatbot/existing_client_details/verticals/issue_escalation/issue_type",methods=["POST"])
def issue_type():
    try:
        issue_type_options = {"1": "Normal", "2": "Urgent"}

        data = request.get_json()
        row_id = data.get("row_id")

        user_response = data.get("user_response")
        if user_response in issue_type_options:
            selected_issue_type = issue_type_options[user_response]

            if selected_issue_type == "Normal":
                response_message = "Thank you. We have saved your issue and will contact you as soon as possible."
            elif selected_issue_type == "Urgent":
                response_message = "Thank you. We have saved your issue as urgent and will contact you immediately."

            query = "UPDATE existing_client SET ISSUE_TYPE = %s WHERE ID = %s"
            values = (selected_issue_type, row_id)
            logging.info(f"issue type saved - {selected_issue_type}")
            cursor.execute(query, values)
            mydb.commit()

            # Extract the new client details from the database
            existing_client_details = extract_existing_client_details()

            # Send email with the existing client details
            if existing_client_details:
                sender_email = os.getenv("sender_email")
                receiver_emails = os.getenv("receiver_emails").split(",")  # Convert comma-separated string to a list
                cc_email = os.getenv("cc_email")
                subject = "Datanetiix chatbot project Email alert testing demo"
                email_message = (
                    f"Hi, one of our client logged in our chatbot, Find the below details for your reference:\n\n"
                    f"Existing client details:\n\n"
                    f"Date: {existing_client_details['date']}\n"
                    f"Time: {existing_client_details['time']}\n"
                    f"IP: {existing_client_details['ip_address']}\n"
                    f"Name: {existing_client_details['name']}\n"
                    f"Email: {existing_client_details['email']}\n"
                    f"Contact: {existing_client_details['contact']}\n"
                    f"Company: {existing_client_details['company']}\n"
                    f"Verticals: {existing_client_details['verticals_choosen']}\n"
                    f"Escalating issue to: {existing_client_details['issue_escalation']}\n"
                    f"Type of issue: {existing_client_details['issue_type']}"
                )
                send_email(sender_email, receiver_emails, cc_email, subject, email_message)

            return jsonify(
                {
                    "user_response": selected_issue_type,
                    "message": response_message,
                    "code": 200,
                }
            )
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API responsible for collecting user details from job seeker and save in DB
@app.route("/chatbot/job_seeker_details", methods=["POST"])
def job_seeker_details():
    try:
        ip_address = get_ip_address()
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        contact = data.get("contact")

        if not is_valid_name(name):
            return jsonify({"message": "Please enter a valid name.", "code": 400})

        if not is_valid_email(email):
            return jsonify({"message": "Please enter a valid email address.", "code": 400})

        if not is_valid_contact_number(contact):
            return jsonify({"message": "Please enter a valid contact number.", "code": 400})

        user_details = {"ip_address":ip_address, "name": name, "email": email, "contact": contact}

        query = "INSERT INTO job_seeker (DATE, TIME, IP_ADDRESS, NAME, EMAIL_ID, CONTACT_NUMBER) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (utc_date, utc_time, ip_address, name, email, contact)
        cursor.execute(query, values)
        row_id = cursor.lastrowid
        mydb.commit()
        logging.info("job seeker contact details saved in DB")
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
    return bool(re.match(r"^\+?\d{1,3}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$",contact))


# this API responsible for collecting user category of job seeker and save in DB
@app.route("/chatbot/job_seeker_details/category", methods=["POST"])
def category():
    try:
        category_type = {"1": "fresher", "2": "experienced"}

        data = request.get_json()
        row_id = data.get("row_id")

        user_type = data.get("user_type")
        if user_type in category_type:
            selected_category_type = category_type[user_type]

            query = "UPDATE job_seeker SET category = %s WHERE ID = %s"
            values = (selected_category_type, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"job seeker category saved - {selected_category_type}")
            return jsonify({"user_type": selected_category_type, "row_id": row_id, "code": 200})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API is responsible for selecting verticals for job seeker and save in DB
@app.route("/chatbot/job_seeker_details/category/verticals", methods=["POST"])
def verticals_job_seeker():
    try:
        verticals = {
            "1": "ML/DS/AI",
            "2": "Sales force",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "Others",
        }

        data = request.get_json()
        row_id = data.get("row_id")

        selected_options = data.get("selected_options", [])
        selected_verticals = [
            verticals[opt] for opt in selected_options if opt in verticals
        ]

        vertical_str = ",".join(selected_verticals)

        query = "UPDATE job_seeker SET VERTICAL = %s WHERE ID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"job seeker vertical saved - {selected_verticals}")
        return jsonify({"selected_verticals": selected_verticals, "code": 200})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API responsible for checking user availability for an interview
@app.route("/chatbot/job_seeker_details/category/verticals/interview_avail", methods=["POST"])
def interview_available_check():
    try:
        interview_avail_options = {"1": "Yes", "2": "No"}

        data = request.get_json()
        row_id = data.get("row_id")

        user_response = data.get("user_response")
        if user_response in interview_avail_options:
            selected_interview_avail = interview_avail_options[user_response]

            query = "UPDATE job_seeker SET INTERVIEW_AVAILABLE = %s WHERE ID = %s"
            values = (selected_interview_avail, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"interview availability checked - {selected_interview_avail}")
            return jsonify(
                {
                    "selected_interview_avail": selected_interview_avail,
                    "row_id": row_id,
                    "code": 200,
                }
            )
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API responsible for checking date for an interview
# in the frontend we have to provide calender
@app.route("/chatbot/job_seeker_details/category/verticals/interview_avail/date_of_interview",methods=["POST"])
def date_of_interview():
    try:
        data = request.get_json()
        row_id = data.get("row_id")
        interview_date = data.get("interview_date")

        query = "UPDATE job_seeker SET TIME_AVAILABLE = %s WHERE ID = %s"
        values = (interview_date, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"intervie date available collected - {interview_date}")
        return jsonify(
            {"interview_date": interview_date, "row_id": row_id, "code": 200}
        )
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500
    

# this API responsible for checking notice period
@app.route("/chatbot/job_seeker_details/category/verticals/interview_avail/date_of_interview/notice_period",methods=["POST"])
def notice_period():
    try:
        notice_period_options = {"1": "30 days", "2": "60 days", "3": "90 days"}
        data = request.get_json()
        row_id = data.get("row_id")

        joining_date = data.get("joining_date")
        if joining_date in notice_period_options:
            selected_notice_period_options = notice_period_options[joining_date]

            query = "UPDATE job_seeker SET NOTICE_PERIOD = %s WHERE ID = %s"
            values = (selected_notice_period_options, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"notice period collected - {selected_notice_period_options}")
            # Extract the new client details from the database
            job_seeker_details = extract_job_seeker_details()

            if job_seeker_details:
                # Send email with the job seeker details
                sender_email = os.getenv("sender_email")
                receiver_emails = os.getenv("receiver_emails").split(",")  # Convert comma-separated string to a list
                cc_email = os.getenv("cc_email")
                subject = "Datanetiix chatbot project Email alert testing demo"
                email_message = (
                    f"Hi, New job seeker logged in our chatbot, Find the below details for your reference:\n\n"
                    f"Job Seeker details:\n\n"
                    f"Date: {job_seeker_details['date']}\n"
                    f"Time: {job_seeker_details['time']}\n"
                    f"IP: {job_seeker_details['ip_address']}\n"
                    f"Name: {job_seeker_details['name']}\n"
                    f"Email: {job_seeker_details['email']}\n"
                    f"Contact: {job_seeker_details['contact']}\n"
                    f"User category: {job_seeker_details['category']}\n"
                    f"Verticals: {job_seeker_details['verticals_choosen']}\n"
                    f"Available for Interview: {job_seeker_details['interview_available']}\n"
                    f"Available date for interview: {job_seeker_details['time_available']}\n"
                    f"Notice period: {job_seeker_details['notice_period']}"
                )
                send_email(sender_email, receiver_emails, cc_email, subject, email_message)

            return jsonify(
                {
                    "joining_date": selected_notice_period_options,
                    "row_id": row_id,
                    "code": 200,
                }
            )
        else:
            return jsonify({"error": "Invalid input. Please select a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
