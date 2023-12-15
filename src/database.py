import mysql.connector as conn
import datetime
import sys
import os
from dotenv import load_dotenv
from src.exception import CustomException
from src.logger import logging


def configure():
    load_dotenv()


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
    


    

create_database()