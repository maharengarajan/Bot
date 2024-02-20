import mysql.connector as conn
import sys
import os
from dotenv import load_dotenv
from src.exception import CustomException
from src.logger import logging


def configure():
    load_dotenv()


configure()
host = os.getenv("database_host_name")
user = os.getenv("database_user_name")
password = os.getenv("database_user_password")
database = os.getenv("database_name")


def create_database(host, user, password):
    try:
        mydb = conn.connect(host=host, user=user, password=password)
        cursor = mydb.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS chatbot")
        logging.info("Database created successfully")
    except Exception as e:
        logging.error(f"An error occurred while creating database: {e}")
        raise CustomException(e, sys)
    

def connect_to_mysql_database(host, user, password, database):
    try:
        mydb = conn.connect(host=host, user=user, password=password, database=database)
        logging.info("Connected to MySQL successfully!")
        return mydb
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def create_cursor_object(mydb):
    try:
        cursor = mydb.cursor()
        logging.info("Cursor object obtained successfully!")
        return cursor
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def create_tables(host, user, password, database):
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        table_queries = [
            """
            CREATE TABLE IF NOT EXISTS chatbot.new_client(
                ID INT AUTO_INCREMENT PRIMARY KEY,
                DATE DATE,
                TIME TIME,
                IP_ADDRESS VARCHAR(45),
                NAME VARCHAR(255),
                EMAIL_ID VARCHAR(255),
                CONTACT_NUMBER VARCHAR(255),
                COMPANY_NAME VARCHAR(500),
                INDUSTRY VARCHAR(255),
                VERTICAL VARCHAR(255),
                REQUIREMENTS VARCHAR(255),
                KNOWN_SOURCE VARCHAR(255),
                RATING VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS chatbot.existing_client(
                ID INT AUTO_INCREMENT PRIMARY KEY,
                DATE DATE,
                TIME TIME,
                IP_ADDRESS VARCHAR(45),
                NAME VARCHAR(255),
                EMAIL_ID VARCHAR(255),
                CONTACT_NUMBER VARCHAR(255),
                COMPANY_NAME VARCHAR(500),
                VERTICAL VARCHAR(255),
                ISSUE_ESCALATION VARCHAR(255),
                ISSUE_TYPE VARCHAR(255),
                RATING VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS chatbot.job_seeker(
                ID INT AUTO_INCREMENT PRIMARY KEY,
                DATE DATE,
                TIME TIME,
                IP_ADDRESS VARCHAR(45),
                NAME VARCHAR(255),
                EMAIL_ID VARCHAR(255),
                CONTACT_NUMBER VARCHAR(255),
                CATEGORY VARCHAR(255),
                VERTICAL VARCHAR(255),
                INTERVIEW_AVAILABLE VARCHAR(255),
                TIME_AVAILABLE VARCHAR(255),
                NOTICE_PERIOD VARCHAR(255),
                RATING VARCHAR(255)
            )
            """
        ]

        # Execute table creation queries
        for query in table_queries:
            cursor.execute(query)

        logging.info("Tables and columns created successfully")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e, sys)


def extract_new_client_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        # execute sql query to retrive new_client details
        query = "SELECT * FROM chatbot.new_client ORDER BY id DESC LIMIT 1"  # we can get the row with highest id value
        cursor.execute(query)
        # Fetch the result
        result = cursor.fetchone()  # getting only one row
        if result:
            # Extract the columns from the result
            (
                id,
                date,
                time,
                ip_address,
                name,
                email,
                contact,
                company,
                selected_industry,
                selected_vertical,
                requirement,
                known_source,
                rating,
            ) = result

            # Extracted new_client details stored in dictionary format
            new_client_details = {
                "id": id,
                "date": date,
                "time": time,
                "ip_address":ip_address,
                "name": name,
                "email": email,
                "contact": contact,
                "company": company,          
                "industries_choosen": selected_industry,
                "verticals_choosen": selected_vertical,
                "requirement": requirement,
                "known_source": known_source,
                "rating": rating
            }

            return new_client_details
        
        # Close the cursor and connection
        cursor.close()
        logging.info("cursor connection closed")
        mydb.close()
        logging.info("database closed")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def extract_existing_client_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        # execute sql query to retrive new_client details
        query = "SELECT * FROM chatbot.existing_client ORDER BY id DESC LIMIT 1"  # we can get the row with highest id value
        cursor.execute(query)
        # Fetch the result
        result = cursor.fetchone()  # getting only one row
        if result:
            # Extract the columns from the result
            (
                id,
                date,
                time,
                ip_address,
                name,
                email,
                contact,
                company,
                selected_vertical,
                issue_escalation,
                issue_type,
                rating
            ) = result

            # Extracted new_client details stored in dictionary format
            existing_client_details = {
                "id": id,
                "date": date,
                "time": time,
                "ip_address":ip_address,
                "name": name,
                "email": email,
                "contact": contact,
                "company": company,
                "verticals_choosen": selected_vertical,
                "issue_escalation": issue_escalation,
                "issue_type": issue_type,
                "rating": rating,
            }

            return existing_client_details
        
        # Close the cursor and connection
        cursor.close()
        logging.info("cursor connection closed")
        mydb.close()
        logging.info("database closed")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def extract_job_seeker_details():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)
        # execute sql query to retrive new_client details
        query = "SELECT * FROM chatbot.job_seeker ORDER BY id DESC LIMIT 1"  # we can get the row with highest id value
        cursor.execute(query)
        # Fetch the result
        result = cursor.fetchone()  # getting only one row
        if result:
            # Extract the columns from the result
            (
                id,
                date,
                time,
                ip_address,
                name,
                email,
                contact,
                category,
                selected_vertical,
                interview_available,
                time_available,
                notice_period,
                rating,
            ) = result

            # Extracted job_seeker details stored in dictionary format
            job_seeker_details = {
                "id": id,
                "date": date,
                "time": time,
                "ip_address":ip_address,
                "name": name,
                "email": email,
                "contact": contact,
                "category": category,
                "verticals_choosen": selected_vertical,
                "interview_available": interview_available,
                "time_available": time_available,
                "notice_period": notice_period,
                "rating": rating,
            }

            return job_seeker_details
        
        # Close the cursor and connection
        cursor.close()
        logging.info("cursor connection closed")
        mydb.close()
        logging.info("database closed")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    


# to create DB and tables execute below command in terminal
# create_database(host, user, password)
# create_tables(host, user, password,database)