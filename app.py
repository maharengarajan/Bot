import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from src.bot.alert import send_email
from src.bot.database import (
    create_tables,
    create_database,
    extract_new_client_details,
    extract_existing_client_details,
    extract_job_seeker_details,
    connect_to_mysql_database,
    create_cursor_object
)
from src.bot.utils import (
    get_current_utc_datetime,
    extract_utc_date_and_time,
    is_valid_name,
    is_valid_email,
    is_valid_contact_number
)
from src.bot.greet import (
    get_ip_address,
    get_location,
    get_weather,
    weather_greeting
)
from src.bot.logger import logging
# import ssl



app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)


def configure():
    load_dotenv()

configure()
host = os.getenv("database_host_name")
user = os.getenv("database_user_name")
password = os.getenv("database_user_password")
database = os.getenv("database_name")
# CERT_FILE = os.getenv("CERT_FILE")
# KEY_FILE = os.getenv("KEY_FILE")


# this api is responsible for creating a database
@app.route('/create_database', methods=['POST'])
def create_database_api():
    try:
        data = request.get_json()
        host = data.get('host')
        user = data.get('user')
        password = data.get('password')

        result = create_database(host, user, password)
        return jsonify(result, {"status": "success", "message": "DB created successfully"})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error", "error": str(e)}), 500


# the below API is responsible for create tables
@app.route('/create_tables', methods=['POST'])
def create_tables_api():
    try:
        data = request.get_json()
        host = data.get('host')
        user = data.get('user')
        password = data.get('password')
        database = data.get('database')

        result = create_tables(host, user, password, database)
        return jsonify(result, {"status": "success", "message": "Tables created successfully"})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error", "error": str(e)}), 500
    

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
        return jsonify({"status": "error", "message": "Internal Server Error", "error": str(e)}), 500
    

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
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API responsible for collecting user details from new client and save in DB
@app.route("/chatbot/new_client_details", methods=["POST"])
def new_client_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        current_utc_datetime = get_current_utc_datetime()
        utc_date, utc_time = extract_utc_date_and_time(current_utc_datetime)
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
        logging.info(f"user details saved in database - {user_details}")
        return jsonify(
            {
                "message": "User details collected successfully.",
                "row_id": row_id,
                "code": 200,
            }
        )
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API is responsible for selecting industries
@app.route("/chatbot/new_client/user_details/industries", methods=["POST"])
def industries():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        industries = {
            "1": "Insurance",
            "2": "Banking",
            "3": "Finance",
            "4": "Logistics",
            "5": "Healthcare",
            "6": "Manufacturing",
            "7": "Ecommerce",
            "8": "Technology",
            "9": "Automobile",
            "10": "Others",
        }
        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        user_input = data.get("selected_options", [])
        user_selected_industries = []
        
        for opt in user_input:
            if opt in industries:
                if opt == '10':
                    source_specification = data.get("source_specification")
                    user_selected_industries.append(industries[opt] + " : " + source_specification)
                else:
                    user_selected_industries.append(industries[opt])

        industry_str = ",".join(user_selected_industries)  # Convert lists to strings

        query = "UPDATE new_client SET INDUSTRY = %s WHERE ID = %s"
        values = (industry_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"new client industry saved in DB - {industry_str}")
        return jsonify({"selected_industries": user_selected_industries, "code": 200})
    
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting verticals
@app.route("/chatbot/new_client/user_details/industries/verticals", methods=["POST"])
def verticals_new_client():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        verticals = {
            "1": "Data and AI",
            "2": "IT Infrastructure",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "Sales force", 
            "6": "Others",
        }

        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        user_input = data.get("selected_options", [])
        user_selected_verticals = []
        
        for opt in user_input:
            if opt in verticals:
                if opt == '6':
                    source_specification = data.get("source_specification")
                    user_selected_verticals.append(verticals[opt] + " : " + source_specification)
                else:
                    user_selected_verticals.append(verticals[opt])

        vertical_str = ",".join(user_selected_verticals)

        query = "UPDATE new_client SET VERTICAL = %s WHERE ID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"new client vertical saved in DB - {vertical_str}")
        return jsonify({"selected_verticals": user_selected_verticals, "code": 200})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting requirements
@app.route("/chatbot/new_client/user_details/industries/verticals/requirement",methods=["POST"])
def requirement():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        requirements = {
            "1": "Start the project from scratch",
            "2": "Require support from existing project",
            "3": "Looking for some kind of solutions",
            "4": "Others",
        }

        data = request.get_json()
        user_selected_option = data.get("selected_option")
        row_id = data.get("row_id")  # Get the user ID from the request
        

        if user_selected_option in requirements:
            if user_selected_option == '4':
                requirement_specification = data.get("requirement_specification")
                selected_requirement = requirements[user_selected_option] + " : " + requirement_specification
            else:
                selected_requirement = requirements[user_selected_option]

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
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting known sources
@app.route("/chatbot/new_client/user_details/industries/verticals/requirement/known_source",methods=["POST"])
def known_source():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        known_sources = {
            "1": "Google",
            "2": "LinkedIn",
            "3": "Email Campaign",
            "4": "News Letter",
            "5": "Hope you get to know about us from ? ",
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
            return jsonify({"selected_known_source": selected_known_source, "code": 200})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API responsible for getting new client rating about our chatbot
@app.route('/chatbot/new_client/user_details/industries/verticals/requirement/known_source/rate', methods=['POST'])
def get_rating_new_client():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        credentials = {
    '1': 'Requires Improvement',
    '2': 'Acceptable',
    '3': 'Above Average',
    '4': 'Excellent',
    '5': 'Outstanding'
}
        data = request.get_json()
        selected_option = data.get('selected_option')
        row_id = data.get("row_id")  # Get the user ID from the request

        if selected_option in credentials:
            user_select = str(credentials[selected_option])
            response = {'status': 'success', 'message':  user_select, 'code': 200}

            query = "UPDATE new_client SET RATING = %s WHERE ID = %s"
            values = (user_select, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"new client star rating saved in DB - {user_select}")

            #extract new client details
            new_client_details = extract_new_client_details()
            logging.info("new client details extracted")

            # Send email with the new client details
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
                    f"Known Source: {new_client_details['known_source']}\n"
                    f"Rating: {new_client_details['rating']}"
                )
                send_email(sender_email,receiver_emails, cc_email, subject, email_message)
            logging.info("mail sent successfully")
        else:
            response = {'status': 'error', 'message': 'Invalid option. Please choose from 1 to 5.'}
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for collecting user details
@app.route("/chatbot/existing_client_details", methods=["POST"])
def existing_client_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        current_utc_datetime = get_current_utc_datetime()
        utc_date, utc_time = extract_utc_date_and_time(current_utc_datetime)
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
        logging.info(f"existing client user details save in DB - {user_details}")
        return jsonify(
            {
                "message": "User details collected successfully.",
                "row_id": row_id,
                "code": 200,
            }
        )
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API is responsible for selecting verticals for existing client and save in DB
@app.route("/chatbot/existing_client_details/verticals", methods=["POST"])
def verticals_exixting_client():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        verticals = {
            "1": "ML/DS/AI",
            "2": "Sales force",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "IT Infrastructure",
            "6": "Others",
        }

        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        user_input = data.get("selected_options", [])
        user_selected_verticals = []
        
        for opt in user_input:
            if opt in verticals:
                if opt == '6':
                    source_specification = data.get("source_specification")
                    user_selected_verticals.append(verticals[opt] + " : " + source_specification)
                else:
                    user_selected_verticals.append(verticals[opt])

        vertical_str = ",".join(user_selected_verticals)

        query = "UPDATE existing_client SET VERTICAL = %s WHERE ID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"existing client vertical saved in DB - {vertical_str}")
        return jsonify({"selected_verticals": user_selected_verticals, "code": 200})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting issue_escalation for existing client and save in DB
@app.route("/chatbot/existing_client_details/verticals/issue_escalation", methods=["POST"])
def issue_escalation():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
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
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting issue_type for existing client and save in DB
@app.route("/chatbot/existing_client_details/verticals/issue_escalation/issue_type",methods=["POST"])
def issue_type():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
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
            logging.info(f"existing client issue type saved - {selected_issue_type}")
            cursor.execute(query, values)
            mydb.commit()

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
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for getting existing client rating about our chatbot
@app.route('/chatbot/existing_client_details/verticals/issue_escalation/issue_type/rate', methods=['POST'])
def get_rating_existing_client():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        credentials = {
    '1': 'Requires Improvement',
    '2': 'Acceptable',
    '3': 'Above Average',
    '4': 'Excellent',
    '5': 'Outstanding'
}
        data = request.get_json()
        selected_option = data.get('selected_option')
        row_id = data.get('row_id') 
        if selected_option in credentials:
            user_selected = str(credentials[selected_option])
            response = {'status': 'success', 'message':  user_selected, 'code': 200}

            query = "UPDATE existing_client SET RATING = %s WHERE ID = %s"
            values = (user_selected, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"existing client star rating saved in DB - {user_selected}")

            # Extract the new client details from the database
            existing_client_details = extract_existing_client_details()
            logging.info("existing client details extracted successfully")

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
                    f"Type of issue: {existing_client_details['issue_type']}\n"
                    f"Rating: {existing_client_details['rating']}"
                )
                send_email(sender_email, receiver_emails, cc_email, subject, email_message)

        else:
            response = {'status': 'error', 'message': 'Invalid option. Please choose from 1 to 5.'}
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for collecting user details from job seeker and save in DB
@app.route("/chatbot/job_seeker_details", methods=["POST"])
def job_seeker_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        current_utc_datetime = get_current_utc_datetime()
        utc_date, utc_time = extract_utc_date_and_time(current_utc_datetime)
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
        logging.info(f"job seeker contact details saved in DB - {user_details}")
        return jsonify(
            {
                "message": "User details collected successfully.",
                "row_id": row_id,
                "code": 200,
            }
        )
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for collecting user category of job seeker and save in DB
@app.route("/chatbot/job_seeker_details/category", methods=["POST"])
def category():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        category_type = {"1": "Fresher", "2": "Experienced", "3": "External consultant"}

        data = request.get_json()
        row_id = data.get("row_id")

        user_type = data.get("user_type")
        if user_type in category_type:
            selected_category_type = category_type[user_type]

            query = "UPDATE job_seeker SET CATEGORY = %s WHERE ID = %s"
            values = (selected_category_type, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"job seeker category saved - {selected_category_type}")
            return jsonify({"user_type": selected_category_type, "row_id": row_id, "code": 200})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting verticals for job seeker and save in DB
@app.route("/chatbot/job_seeker_details/category/verticals", methods=["POST"])
def verticals_job_seeker():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        verticals = {
            "1": "ML/DS/AI",
            "2": "Sales force",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "IT Infrastructure",
            "6": "Others",
        }

        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        user_input = data.get("selected_options", [])
        user_selected_verticals = []
        
        for opt in user_input:
            if opt in verticals:
                if opt == '6':
                    source_specification = data.get("source_specification")
                    user_selected_verticals.append(verticals[opt] + " : " + source_specification)
                else:
                    user_selected_verticals.append(verticals[opt])

        vertical_str = ",".join(user_selected_verticals)

        query = "UPDATE job_seeker SET VERTICAL = %s WHERE ID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"job seeker vertical saved in DB - {vertical_str}")
        return jsonify({"selected_verticals": user_selected_verticals, "code": 200})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API responsible for checking user availability for an interview
@app.route("/chatbot/job_seeker_details/category/verticals/interview_avail", methods=["POST"])
def interview_available_check():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
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
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API responsible for checking date for an interview
@app.route("/chatbot/job_seeker_details/category/verticals/interview_avail/date_of_interview",methods=["POST"])
def date_of_interview():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
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
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API responsible for checking notice period
@app.route("/chatbot/job_seeker_details/category/verticals/interview_avail/date_of_interview/notice_period",methods=["POST"])
def notice_period():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        notice_period_options = {"1": "Below 30 days", "2": "30 days", "3": "60 days", "4": "90 days"}
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
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for getting job seeker rating about our chatbot
@app.route('/chatbot/job_seeker_details/category/verticals/interview_avail/date_of_interview/notice_period/rate', methods=['POST'])
def get_rating_job_seeker():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        credentials = {
    '1': 'Requires Improvement',
    '2': 'Acceptable',
    '3': 'Above Average',
    '4': 'Excellent',
    '5': 'Outstanding'
}
        data = request.get_json()
        selected_option = data.get('selected_option')
        row_id = data.get('row_id') 
        if selected_option in credentials:
            user_selected = str(credentials[selected_option])
            response = {'status': 'success', 'message':  user_selected, 'code': 200}

            query = "UPDATE job_seeker SET RATING = %s WHERE ID = %s"
            values = (user_selected, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"job seeker star rating saved in DB - {user_selected}")

            #Extract the new client details from the database
            job_seeker_details = extract_job_seeker_details()
            logging.info("job seeker conversation extracted")

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
                    f"Notice period: {job_seeker_details['notice_period']}\n"
                    f"Rating: {job_seeker_details['rating']}"
                )
                send_email(sender_email, receiver_emails, cc_email, subject, email_message)

        else:
            response = {'status': 'error', 'message': 'Invalid option. Please choose from 1 to 5.'}
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# context=  ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
# context.load_cert_chain(CERT_FILE,KEY_FILE)


if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True,port=8000)
    # app.run(host="0.0.0.0",debug=True,port=9600,ssl_context=context)

