import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from src.bot.alert import send_email
from src.bot.database import (
    create_tables,
    create_database,
    extract_prospect_conversation,
    extract_existing_client_conversation,
    extract_job_seeker_conversation,
    connect_to_mysql_database,
    create_cursor_object,
    get_smtp_credentials
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
            "1": "Welcome, Prospects!",
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
    

## this API responsible for collecting user details from prospects and save in DB
@app.route("/chatbot/prospect", methods=["POST"])
def prospect_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        current_utc_datetime = get_current_utc_datetime()
        utc_date, utc_time = extract_utc_date_and_time(current_utc_datetime)
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        contact = data.get("contact")
        company = data.get("company")
        ip = data.get("ip")  # this IP captured by frontend code

        if not is_valid_name(name):
            return jsonify({"message": "Please enter a valid name.", "code": 400})

        if not is_valid_email(email):
            return jsonify({"message": "Please enter a valid email address.", "code": 400})

        if not is_valid_contact_number(contact):
            return jsonify({"message": "Please enter a valid contact number.", "code": 400})

        user_details = {"ip_address":ip, "name": name, "email": email, "contact": contact, "company":company}

        query = "INSERT INTO PROSPECTS (CREATED_ON, CREATED_TIME, IP, NAME, EMAIL_ID, CONTACT_NUMBER, COMPANY_NAME) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (utc_date, utc_time, ip, name, email, contact, company, )
        cursor.execute(query, values)
        row_id = cursor.lastrowid  # Get the ID (primary key) of the inserted row
        mydb.commit()  # Commit the changes to the database
        logging.info(f"prospect details saved in database - {user_details}")
        return jsonify(
            {
                "message": "prospect details collected successfully.",
                "row_id": row_id,
                "code": 200,
            }
        )
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


## this API is responsible for selecting industries for prospect
@app.route("/chatbot/prospect/industries", methods=["POST"])
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
            "9": "Automotive",
            "10": "Retail",
            "11": "Others",
        }
        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        user_input = data.get("selected_options", [])
        user_selected_industries = []
        
        for opt in user_input:
            if opt in industries:
                if opt == '11':
                    source_specification = data.get("source_specification")
                    user_selected_industries.append(industries[opt] + " : " + source_specification)
                else:
                    user_selected_industries.append(industries[opt])

        industry_str = ",".join(user_selected_industries)  # Convert lists to strings

        query = "UPDATE prospects SET INDUSTRY = %s WHERE PID = %s"
        values = (industry_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"industry saved in DB - {industry_str}")
        return jsonify({"selected_industries": user_selected_industries, "code": 200, "row_id": row_id,})
    
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting verticals
@app.route("/chatbot/prospect/verticals", methods=["POST"])
def verticals_prospect():
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
        row_id = data.get("row_id")

        selected_option = data.get("selected_option")

        if selected_option not in verticals:
            raise ValueError("Invalid selection")

        if selected_option == '6':
            source_specification = data.get("source_specification")
            user_selected_vertical = verticals[selected_option] + " : " + source_specification
        else:
            user_selected_vertical = verticals[selected_option]

        query = "UPDATE prospects SET VERTICAL = %s WHERE PID = %s"
        values = (user_selected_vertical, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"vertical saved in DB - {user_selected_vertical}")
        return jsonify({"selected_vertical": user_selected_vertical, "code": 200, "row_id": row_id,})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting requirements for AI & custom app
@app.route("/chatbot/prospect/ai_requirement",methods=["POST"])
def requirement():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        requirements = {
            "1": "Develop a new project",
            "2": "Enhance an existing project",
            "3": "Project consultation or troubleshooting",
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

            query = "UPDATE prospects SET REQUIREMENTS = %s WHERE PID = %s"
            values = (selected_requirement, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"prospect requirement saved in DB - {selected_requirement}")
            return jsonify({"selected_requirement": selected_requirement, "code": 200, "row_id": row_id,})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500



# this API is responsible for selecting requirements for MD365
@app.route("/chatbot/prospect/md_requirement",methods=["POST"])
def md_requirement():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        requirements = {
            "1": "New Implementation / Re-implementation",
            "2": "Version Upgrades",
            "3": "Support Services",
            "4": "Integration Services",
            "5": "Others",
        }

        data = request.get_json()
        user_selected_option = data.get("selected_option")
        row_id = data.get("row_id")  # Get the user ID from the request
        

        if user_selected_option in requirements:
            if user_selected_option == '5':
                requirement_specification = data.get("requirement_specification")
                selected_requirement = requirements[user_selected_option] + " : " + requirement_specification
            else:
                selected_requirement = requirements[user_selected_option]

            query = "UPDATE prospects SET REQUIREMENTS = %s WHERE PID = %s"
            values = (selected_requirement, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"new client requirement saved in DB - {selected_requirement}")
            return jsonify({"selected_requirement": selected_requirement, "code": 200, "row_id": row_id,})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting requirements for salesforce
@app.route("/chatbot/prospect/sf_requirement",methods=["POST"])
def sf_requirement():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        requirements = {
            "1": "New Implementation / Re-implementation",
            "2": "Platform Migration",
            "3": "Support Services",
            "4": "Integration Services",
            "5": "Others",
        }

        data = request.get_json()
        user_selected_option = data.get("selected_option")
        row_id = data.get("row_id")  # Get the user ID from the request
        

        if user_selected_option in requirements:
            if user_selected_option == '5':
                requirement_specification = data.get("requirement_specification")
                selected_requirement = requirements[user_selected_option] + " : " + requirement_specification
            else:
                selected_requirement = requirements[user_selected_option]

            query = "UPDATE prospects SET REQUIREMENTS = %s WHERE PID = %s"
            values = (selected_requirement, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"new client requirement saved in DB - {selected_requirement}")
            return jsonify({"selected_requirement": selected_requirement, "code": 200, "row_id": row_id,})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500



# this API is responsible for selecting requirements for IT
@app.route("/chatbot/prospect/it_requirement",methods=["POST"])
def it_requirement():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        requirements = {
            "1": "Infrastructure support",
            "2": "Maintenance and Troubleshooting",
            "3": "Implementation and Migration",
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

            query = "UPDATE prospects SET REQUIREMENTS = %s WHERE PID = %s"
            values = (selected_requirement, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"new client requirement saved in DB - {selected_requirement}")
            return jsonify({"selected_requirement": selected_requirement, "code": 200, "row_id": row_id,})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API is responsible for selecting known sources
@app.route("/chatbot/prospect/known_source",methods=["POST"])
def known_source():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        known_sources = {
            "1": "Google",
            "2": "LinkedIn",
            "3": "Email Campaign",
            "4": "News Letter",
            "5": "Reference",
            "6": "Others",
        }

        data = request.get_json()
        selected_option = data.get("selected_option")
        row_id = data.get("row_id")  # Get the user ID from the request

        if selected_option in known_sources:
            if selected_option in ["5", "6"]:
                source_specification = request.get_json().get("source_specification")
                # selected_known_source = (known_sources[selected_option] + " : " + source_specification)
                selected_known_source = source_specification
            else:
                selected_known_source = known_sources[selected_option]

            query = "UPDATE prospects SET KNOWN_SOURCE = %s WHERE PID = %s"
            values = (selected_known_source, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"known source saved in DB - {selected_known_source}")
            return jsonify({"selected_known_source": selected_known_source, "code": 200, "row_id": row_id,})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API responsible for getting new client rating about our chatbot
@app.route('/chatbot/prospect/rate', methods=['POST'])
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
            response = {'status': 'success', 'message':  user_select, 'code': 200, "row_id": row_id,}

            query = "UPDATE prospects SET RATING = %s WHERE PID = %s"
            values = (user_select, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"new client star rating saved in DB - {user_select}")
        else:
            response = {'status': 'error', 'message': 'Invalid option. Please choose from 1 to 5.'}
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this api responsible for getting feedback from prospect
@app.route('/chatbot/prospect/feedback', methods=['POST'])
def save_feedback():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        data = request.get_json()
        feedback_text = data.get('text')
        row_id = data.get("row_id")  # Get the user ID from the request
        query = "UPDATE prospects SET FEEDBACK = %s WHERE PID = %s"
        values = (feedback_text, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info("prospect feedback saved in Db")

        # extract prospect conversation
        prospect_conversation = extract_prospect_conversation()
        logging.info("new client details extracted")

        # get smtp credentials
        smtp_credentials = get_smtp_credentials(host, user, password, database)
        logging.info("smtp credentials extracted from DB")

        # Send email with prospect converastion
        if prospect_conversation:
            prospect_email_message = (
                f"Hi, new user logged in our chatbot, Find the below details for your reference:\n\n"
                f"New client details:\n\n"
                f"Date: {prospect_conversation['date']}\n"
                f"Time: {prospect_conversation['time']}\n"
                f"IP: {prospect_conversation['ip_address']}\n"
                f"Name: {prospect_conversation['name']}\n"
                f"Email: {prospect_conversation['email']}\n"
                f"Contact: {prospect_conversation['contact']}\n"
                f"Company: {prospect_conversation['company']}\n"
                f"Industries: {prospect_conversation['industries_choosen']}\n"
                f"Verticals: {prospect_conversation['verticals_choosen']}\n"
                f"Requirements: {prospect_conversation['requirement']}\n"
                f"Known Source: {prospect_conversation['known_source']}\n"
                f"Rating: {prospect_conversation['rating']}\n"
                f"Feedback: {prospect_conversation['feedback']}"
                )
            send_email(smtp_credentials['sender_email'], smtp_credentials['prospect_receiver_emails'], smtp_credentials['cc_email'], smtp_credentials['prospect_email_subject'], prospect_email_message)
            logging.info("mail sent successfully")

        return jsonify({'message': 'Feedback saved successfully', 'feedback': feedback_text, "row_id": row_id,}), 200
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for collecting user details for existing client
@app.route("/chatbot/existing_client", methods=["POST"])
def existing_client_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        current_utc_datetime = get_current_utc_datetime()
        utc_date, utc_time = extract_utc_date_and_time(current_utc_datetime)
        # ip_address = get_ip_address()
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        contact = data.get("contact")
        company = data.get("company")
        ip = data.get("ip")

        if not is_valid_name(name):
            return jsonify({"message": "Please enter a valid name.", "code": 400})

        if not is_valid_email(email):
            return jsonify({"message": "Please enter a valid email address.", "code": 400})

        if not is_valid_contact_number(contact):
            return jsonify({"message": "Please enter a valid contact number.", "code": 400})

        user_details = {"ip_address":ip, "name": name, "email": email, "contact": contact, "company": company}

        query = "INSERT INTO existing_client (CREATED_ON, CREATED_TIME, IP, NAME, EMAIL_ID, CONTACT_NUMBER, COMPANY_NAME) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (utc_date, utc_time, ip, name, email, contact, company)
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
@app.route("/chatbot/existing_client/verticals", methods=["POST"])
def verticals_exixting_client():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        verticals = {
            "1": "Data and AI",
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

        query = "UPDATE existing_client SET VERTICAL = %s WHERE EID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"existing client vertical saved in DB - {vertical_str}")
        return jsonify({"selected_verticals": user_selected_verticals, "code": 200, "row_id": row_id})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting issue_escalation for existing client and save in DB
@app.route("/chatbot/existing_client/issue_escalation", methods=["POST"])
def issue_escalation():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        issue_escalation_options = {
            "1": "Sales",
            "2": "Support",
        }

        data = request.get_json()
        row_id = data.get("row_id")

        selected_option = data.get("selected_option")
        if selected_option in issue_escalation_options:
            selected_issue_escalation = issue_escalation_options[selected_option]

            query = "UPDATE existing_client SET ISSUE_ESCALATION = %s WHERE EID = %s"
            values = (selected_issue_escalation, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"issue escalation selected - {selected_issue_escalation}")
            return jsonify(
                {"selected_isse_type": selected_issue_escalation, "code": 200, "row_id": row_id}
            )
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this API is responsible for selecting issue_type for existing client and save in DB
@app.route("/chatbot/existing_client/issue_type",methods=["POST"])
def issue_type():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        issue_type_options = {"1": "Low", "2": "Medium", "3": "High"}

        data = request.get_json()
        row_id = data.get("row_id")

        user_response = data.get("user_response")
        if user_response in issue_type_options:
            selected_issue_type = issue_type_options[user_response]

            # if selected_issue_type == "Normal":
            #     response_message = "Thank you. We have saved your issue and will contact you as soon as possible."
            # elif selected_issue_type == "Urgent":
            #     response_message = "Thank you. We have saved your issue as urgent and will contact you immediately."

            query = "UPDATE existing_client SET ISSUE_TYPE = %s WHERE EID = %s"
            values = (selected_issue_type, row_id)
            logging.info(f"existing client issue type saved - {selected_issue_type}")
            cursor.execute(query, values)
            mydb.commit()

            return jsonify(
                {
                    "user_response": selected_issue_type,
                    "row_id": row_id,
                    "code": 200,
                }
            )
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this APi is responsible for collecting issue as a text
@app.route('/chatbot/existing_client/collect_issue', methods=['POST'])
def collect_issue():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        data = request.get_json()
        issue = data.get('issue')
        row_id = data.get("row_id")  # Get the user ID from the request
        query = "UPDATE existing_client SET ISSUE_TEXT = %s WHERE EID = %s"
        values = (issue, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info("client issue saved in Db")
        return jsonify({'message': 'client issue saved', 'issue': issue, "row_id": row_id}), 200
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for getting existing client rating about our chatbot
@app.route('/chatbot/existing_client/rate', methods=['POST'])
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
            response = {'status': 'success', 'message':  user_selected, 'code': 200, "row_id": row_id}

            query = "UPDATE existing_client SET RATING = %s WHERE EID = %s"
            values = (user_selected, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"existing client star rating saved in DB - {user_selected}")
        
        else:
            response = {'status': 'error', 'message': 'Invalid option. Please choose from 1 to 5.'}
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this api responsible for getting feedback from prospect
@app.route('/chatbot/existing_client/feedback', methods=['POST'])
def save_client_feedback():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        data = request.get_json()
        feedback_text = data.get('text')
        row_id = data.get("row_id")  # Get the user ID from the request
        query = "UPDATE existing_client SET FEEDBACK = %s WHERE EID = %s"
        values = (feedback_text, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info("ckient feedback saved in Db")

        # extract prospect conversation
        existing_client_conversation = extract_existing_client_conversation()
        logging.info("new client details extracted")

        # get smtp credentials
        smtp_credentials = get_smtp_credentials(host, user, password, database)
        logging.info("smtp credentials extracted from DB")

        # Send email with prospect converastion
        if existing_client_conversation:
            client_email_message = (
                f"Hi, one of our client logged in our chatbot, Find the below details for your reference:\n\n"
                f"Client details:\n\n"
                f"Date: {existing_client_conversation['date']}\n"
                f"Time: {existing_client_conversation['time']}\n"
                f"IP: {existing_client_conversation['ip_address']}\n"
                f"Name: {existing_client_conversation['name']}\n"
                f"Email: {existing_client_conversation['email']}\n"
                f"Contact: {existing_client_conversation['contact']}\n"
                f"Company: {existing_client_conversation['company']}\n"
                f"Verticals: {existing_client_conversation['verticals_choosen']}\n"
                f"Contact Team: {existing_client_conversation['issue_escalation']}\n"
                f"Issue Urgency: {existing_client_conversation['issue_type']}\n"
                f"Issue description: {existing_client_conversation['issue_text']}\n"
                f"Rating: {existing_client_conversation['rating']}\n"
                f"Feedback: {existing_client_conversation['feedback']}"
                )
            send_email(smtp_credentials['sender_email'],smtp_credentials['existing_client_receiver_emails'], smtp_credentials['cc_email'], smtp_credentials['existing_client_email_subject'], client_email_message)
            # logging.info("mail sent successfully")

        return jsonify({'message': 'Feedback saved successfully', 'feedback': feedback_text, "row_id": row_id}), 200
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for collecting user details from job seeker and save in DB
@app.route("/chatbot/job_seeker", methods=["POST"])
def job_seeker_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        current_utc_datetime = get_current_utc_datetime()
        utc_date, utc_time = extract_utc_date_and_time(current_utc_datetime)
        # ip_address = get_ip_address()
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        contact = data.get("contact")
        company = data.get("company")
        ip = data.get("ip")

        if not is_valid_name(name):
            return jsonify({"message": "Please enter a valid name.", "code": 400})

        if not is_valid_email(email):
            return jsonify({"message": "Please enter a valid email address.", "code": 400})

        if not is_valid_contact_number(contact):
            return jsonify({"message": "Please enter a valid contact number.", "code": 400})

        user_details = {"ip_address":ip, "name": name, "email": email, "contact": contact, "company": company}

        query = "INSERT INTO job_seeker (CREATED_ON, CREATED_TIME, IP, NAME, EMAIL_ID, CONTACT_NUMBER, COMPANY_NAME) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (utc_date, utc_time, ip, name, email, contact, company)
        cursor.execute(query, values)
        row_id = cursor.lastrowid
        mydb.commit()
        logging.info(f"job seeker details saved in DB - {user_details}")
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
@app.route("/chatbot/job_seeker/category", methods=["POST"])
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

            query = "UPDATE job_seeker SET CATEGORY = %s WHERE JID = %s"
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
@app.route("/chatbot/job_seeker/verticals", methods=["POST"])
def verticals_job_seeker():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        verticals = {
            "1": "Data and AI",
            "2": "IT Infrastructure",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "Salesforce",
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

        query = "UPDATE job_seeker SET VERTICAL = %s WHERE JID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"job seeker vertical saved in DB - {vertical_str}")
        return jsonify({"selected_verticals": user_selected_verticals, "code": 200, "row_id": row_id})
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

            query = "UPDATE job_seeker SET INTERVIEW_AVAILABLE = %s WHERE JID = %s"
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
    

# this API responsible for checking mode of an interview
@app.route("/chatbot/job_seeker/interview_mode", methods=["POST"])
def interview_mode():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        interview_mode_options = {"1": "Virtual Interview", "2": "In person Interview"}

        data = request.get_json()
        row_id = data.get("row_id")

        user_response = data.get("user_response")
        if user_response in interview_mode_options:
            selected_interview_mode = interview_mode_options[user_response]

            query = "UPDATE job_seeker SET INTERVIEW_MODE = %s WHERE JID = %s"
            values = (selected_interview_mode, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"interview mode collected - {selected_interview_mode}")
            return jsonify(
                {
                    "selected_interview_mode": selected_interview_mode,
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
@app.route("/chatbot/job_seeker/date_of_interview",methods=["POST"])
def date_of_interview():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        data = request.get_json()
        row_id = data.get("row_id")
        interview_date = data.get("interview_date")

        query = "UPDATE job_seeker SET TIME_AVAILABLE = %s WHERE JID = %s"
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
@app.route("/chatbot/job_seeker/notice_period",methods=["POST"])
def notice_period():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        notice_period_options = {"1": "Immediate Joiner", "2": "Below 30 days", "3": "30 days", "4": "60 days", "5": "90 days"}
        data = request.get_json()
        row_id = data.get("row_id")

        joining_date = data.get("joining_date")
        if joining_date in notice_period_options:
            selected_notice_period_options = notice_period_options[joining_date]

            query = "UPDATE job_seeker SET NOTICE_PERIOD = %s WHERE JID = %s"
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
    

# this API is responsible for collecting linkedin url from the user
@app.route("/chatbot/job_seeker/linkedin_url", methods=['POST'])
def collect_linkedin_url():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)

        data = request.get_json()
        row_id = data.get("row_id")

        linkedin_url = data.get('linkedin_url')
        if linkedin_url:
            query = "UPDATE job_seeker SET LINKEDIN_URL = %s WHERE JID = %s"
            values = (linkedin_url, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"linkedin url collected - {linkedin_url}")
            return jsonify({"message": "LinkedIn URL received",
                            "row_id": row_id, 
                            "linkedin_url": linkedin_url}), 200
        else:
            return jsonify({"error": "No LinkedIn URL provided"}), 400
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# this API responsible for getting job seeker rating about our chatbot
@app.route('/chatbot/job_seeker/rate', methods=['POST'])
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
            response = {'status': 'success', 'message':  user_selected, 'code': 200, "row_id": row_id}

            query = "UPDATE job_seeker SET RATING = %s WHERE JID = %s"
            values = (user_selected, row_id)
            cursor.execute(query, values)
            mydb.commit()
            logging.info(f"job seeker star rating saved in DB - {user_selected}")
        else:
            response = {'status': 'error', 'message': 'Invalid option. Please choose from 1 to 5.'}
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500
    

# this api responsible for getting feedback from prospect
@app.route('/chatbot/job_seeker/jobseeker_feedback', methods=['POST'])
def save_jobseeker_feedback():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        data = request.get_json()
        feedback_text = data.get('text')
        row_id = data.get("row_id")  # Get the user ID from the request
        query = "UPDATE job_seeker SET FEEDBACK = %s WHERE JID = %s"
        values = (feedback_text, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info("ckient feedback saved in Db")

        # extract prospect conversation
        job_seeker_conversation = extract_job_seeker_conversation()
        logging.info("job seeker conversation extracted")

        # get smtp credentials
        smtp_credentials = get_smtp_credentials(host, user, password, database)
        logging.info("smtp credentials extracted from DB")

        # Send email with prospect converastion
        if job_seeker_conversation:
            job_seeker_email_message = (
                f"Hi, New job seeker logged in our chatbot, Find the below details for your reference:\n\n"
                f"Job Seeker details:\n\n"
                f"Date: {job_seeker_conversation['date']}\n"
                f"Time: {job_seeker_conversation['time']}\n"
                f"IP: {job_seeker_conversation['ip_address']}\n"
                f"Name: {job_seeker_conversation['name']}\n"
                f"Email: {job_seeker_conversation['email']}\n"
                f"Contact: {job_seeker_conversation['contact']}\n"
                f"Company: {job_seeker_conversation['company']}\n"
                f"Category: {job_seeker_conversation['category']}\n"
                f"Verticals: {job_seeker_conversation['verticals_choosen']}\n"
                f"Interview mode: {job_seeker_conversation['interview_mode']}\n"
                f"Time availability: {job_seeker_conversation['time_available']}\n"
                f"Notice period: {job_seeker_conversation['notice_period']}\n"
                f"Linkedin URL: {job_seeker_conversation['linkedin_url']}\n"
                f"Rating: {job_seeker_conversation['rating']}\n"
                f"Feedback: {job_seeker_conversation['feedback']}"
                )
            send_email(smtp_credentials['sender_email'],smtp_credentials['job_seeker_receiver_emails'],smtp_credentials['cc_email'],smtp_credentials['job_seeker_email_subject'], job_seeker_email_message)
            logging.info("mail sent successfully")

        return jsonify({'message': 'Feedback saved successfully', 'feedback': feedback_text, "row_id": row_id}), 200
    except Exception as e:
        logging.error(f"Error in processing request: {e}")
        return jsonify({"message": "Internal server error.", "status": "error", "error": str(e)}), 500


# context=  ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
# context.load_cert_chain(CERT_FILE,KEY_FILE)


if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True,port=8000)
    # app.run(host="0.0.0.0",debug=True,port=9600,ssl_context=context)

