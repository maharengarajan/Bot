import mysql.connector as conn
import datetime
import sys
import os
from dotenv import load_dotenv
from src.exception import CustomException
from src.logger import logging


def configure():
    load_dotenv()


configure()
host = os.getenv("database_host_name")
user_name = os.getenv("database_user_name")
password = os.getenv("database_user_password")
database = os.getenv("database_name")


def create_database():
    try:

        configure()

        host = os.getenv("database_host_name")
        user_name = os.getenv("database_user_name")
        password = os.getenv("database_user_password")

        # Connection from Python to MySQL
        mydb = conn.connect(host=host,user=user_name,password=password)

        # Creating a pointer to the MySQL database
        cursor = mydb.cursor()

        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS Bot")

        logging.info("database created successfully")

        # Create tables and columns if they don't exist
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Bot.new_client(ID INT AUTO_INCREMENT PRIMARY KEY, DATE DATE, TIME TIME, IP_ADDRESS VARCHAR(45), NAME VARCHAR(255), EMAIL_ID VARCHAR(255), CONTACT_NUMBER VARCHAR(255), COMPANY_NAME VARCHAR(500), INDUSTRY VARCHAR(255), VERTICAL VARCHAR(255), REQUIREMENTS VARCHAR(255), KNOWN_SOURCE VARCHAR(255))"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Bot.existing_client(ID INT AUTO_INCREMENT PRIMARY KEY, DATE DATE, TIME TIME, IP_ADDRESS VARCHAR(45), NAME VARCHAR(255), EMAIL_ID VARCHAR(255), CONTACT_NUMBER VARCHAR(255), COMPANY_NAME VARCHAR(500), VERTICAL VARCHAR(255), ISSUE_ESCALATION VARCHAR(255), ISSUE_TYPE VARCHAR(255))"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Bot.job_seeker(ID INT AUTO_INCREMENT PRIMARY KEY, DATE DATE, TIME TIME, IP_ADDRESS VARCHAR(45), NAME VARCHAR(255), EMAIL_ID VARCHAR(255), CONTACT_NUMBER VARCHAR(255), CATEGORY VARCHAR(255), VERTICAL VARCHAR(255), INTERVIEW_AVAILABLE VARCHAR(255), TIME_AVAILABLE VARCHAR(255), NOTICE_PERIOD VARCHAR(255))"
        )
        logging.info("Tables and columns created ")

        cursor.close()
        mydb.close()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def extract_new_client_details():
    try:

        # Connection from Python to MySQL
        mydb = conn.connect(host=host,user=user_name,password=password,database=database)

        # Creating a pointer to the MySQL database
        cursor = mydb.cursor()

        # execute sql query to retrive new_client details
        query = "SELECT * FROM new_client ORDER BY id DESC LIMIT 1"  # we can get the row with highest id value
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
            }

            return new_client_details
        
        # Close the cursor and connection
        cursor.close()
        mydb.close()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def extract_existing_client_details():
    try:

        # connection to mysql database
        mydb = conn.connect(host=host,user=user_name,password=password,database=database)

        # create cursor object to execute SQL queries
        cursor = mydb.cursor()

        # execute sql query to retrive new_client details
        query = "SELECT * FROM existing_client ORDER BY id DESC LIMIT 1"  # we can get the row with highest id value
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
            }

            return existing_client_details
        
        # Close the cursor and connection
        cursor.close()
        mydb.close()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def extract_job_seeker_details():
    try:

        # connection to mysql database
        mydb = conn.connect(host=host,user=user_name,password=password,database=database)

        # create cursor object to execute SQL queries
        cursor = mydb.cursor()

        # execute sql query to retrive new_client details
        query = "SELECT * FROM job_seeker ORDER BY id DESC LIMIT 1"  # we can get the row with highest id value
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
            }

            return job_seeker_details
        # Close the cursor and connection
        cursor.close()
        mydb.close()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

    


    
