import mysql.connector as conn
import sys
import os
from dotenv import load_dotenv
from src.bot.exception import CustomException
from src.bot.logger import logging


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
        return True
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
            CREATE TABLE IF NOT EXISTS PROSPECTS(
                PID INT AUTO_INCREMENT PRIMARY KEY,
                CREATED_ON DATE,
                CREATED_TIME TIME,
                IP VARCHAR(45),
                NAME VARCHAR(255),
                EMAIL_ID VARCHAR(255),
                CONTACT_NUMBER VARCHAR(255),
                COMPANY_NAME VARCHAR(255),
                INDUSTRY VARCHAR(255),
                VERTICAL VARCHAR(255),
                REQUIREMENTS VARCHAR(255),
                KNOWN_SOURCE VARCHAR(255),
                RATING VARCHAR(255),
                FEEDBACK VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS EXISTING_CLIENT(
                EID INT AUTO_INCREMENT PRIMARY KEY,
                CREATED_ON DATE,
                CREATED_TIME TIME,
                IP VARCHAR(45),
                NAME VARCHAR(255),
                EMAIL_ID VARCHAR(255),
                CONTACT_NUMBER VARCHAR(255),
                COMPANY_NAME VARCHAR(255),
                VERTICAL VARCHAR(255),
                ISSUE_ESCALATION VARCHAR(255),
                ISSUE_TYPE VARCHAR(255),
                ISSUE_TEXT VARCHAR(255),
                RATING VARCHAR(255),
                FEEDBACK VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS JOB_SEEKER(
                JID INT AUTO_INCREMENT PRIMARY KEY,
                CREATED_ON DATE,
                CREATED_TIME TIME,
                IP VARCHAR(45),
                NAME VARCHAR(255),
                EMAIL_ID VARCHAR(255),
                CONTACT_NUMBER VARCHAR(255),
                COMPANY_NAME VARCHAR(255),
                CATEGORY VARCHAR(255),
                VERTICAL VARCHAR(255),
                INTERVIEW_MODE VARCHAR(255),
                TIME_AVAILABLE VARCHAR(255),
                NOTICE_PERIOD VARCHAR(255),
                LINKEDIN_URL VARCHAR(255),
                RATING VARCHAR(255),
                FEEDBACK VARCHAR(255)
            )
            """
        ]

        # Execute table creation queries
        for query in table_queries:
            cursor.execute(query)

        logging.info("Tables and columns created successfully")
        return True
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e, sys)


def extract_prospect_conversation():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)

        query = "SELECT * FROM PROSPECTS ORDER BY PID DESC LIMIT 1"  # we can get the row with highest id value
        cursor.execute(query)

        result = cursor.fetchone()  # getting only one row
        if result:
            # Extract the columns from the result
            (
                PID,
                CREATED_ON,
                CREATED_TIME,
                IP,
                NAME,
                EMAIL_ID,
                CONTACT_NUMBER,
                COMPANY_NAME,
                INDUSTRY,
                VERTICAL,
                REQUIREMENTS,
                KNOWN_SOURCE,
                RATING,
                FEEDBACK
            ) = result

            # Extracted new_client details stored in dictionary format
            prospect_details = {
                "id": PID,
                "date": CREATED_ON,
                "time": CREATED_TIME,
                "ip_address":IP,
                "name": NAME,
                "email": EMAIL_ID,
                "contact": CONTACT_NUMBER,
                "company": COMPANY_NAME,          
                "industries_choosen": INDUSTRY,
                "verticals_choosen": VERTICAL,
                "requirement": REQUIREMENTS,
                "known_source": KNOWN_SOURCE,
                "rating": RATING,
                "feedback": FEEDBACK
            }

            return prospect_details
        
        # Close the cursor and connection
        cursor.close()
        logging.info("cursor connection closed")
        mydb.close()
        logging.info("database closed")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def extract_existing_client_conversation():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)

        # execute sql query to retrive new_client details
        query = "SELECT * FROM existing_client ORDER BY eid DESC LIMIT 1"  # we can get the row with highest id value
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
                issue_text,
                rating,
                feedback
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
                "issue_text": issue_text,
                "rating": rating,
                "feedback": feedback,
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
    

def extract_job_seeker_conversation():
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)

        # execute sql query to retrive new_client details
        query = "SELECT * FROM job_seeker ORDER BY JID DESC LIMIT 1"  # we can get the row with highest id value
        cursor.execute(query)
        # Fetch the result
        result = cursor.fetchone()  # getting only one row
        if result:
            # Extract the columns from the result
            (
                PID,
                CREATED_ON,
                CREATED_TIME,
                IP,
                NAME,
                EMAIL_ID,
                CONTACT_NUMBER,
                COMPANY_NAME,
                CATEGORY,
                VERTICAL,
                INTERVIEW_MODE,
                TIME_AVAILABLE,
                NOTICE_PERIOD,
                LINKEDIN_URL,
                RATING,
                FEEDBACK,
            ) = result

            # Extracted job_seeker details stored in dictionary format
            job_seeker_details = {
                "id": PID,
                "date": CREATED_ON,
                "time": CREATED_TIME,
                "ip_address":IP,
                "name": NAME,
                "email": EMAIL_ID,
                "contact": CONTACT_NUMBER,
                "company": COMPANY_NAME,
                "category": CATEGORY,
                "verticals_choosen": VERTICAL,
                "interview_mode": INTERVIEW_MODE,
                "time_available": TIME_AVAILABLE,
                "notice_period": NOTICE_PERIOD,
                "linkedin_url": LINKEDIN_URL,
                "rating": RATING,
                "feedback": FEEDBACK,
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


def alter_table(host, user, password, database):
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)

        alter_table_query = """
                            ALTER TABLE job_seeker 
                            ADD COLUMN INTERVIEW_MODE VARCHAR(255) AFTER INTERVIEW_AVAILABLE,
                            ADD COLUMN LINKEDIN_URL VARCHAR(255) AFTER NOTICE_PERIOD
                            """
        cursor.execute(alter_table_query)
        logging.info("Columns added successfully")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def get_smtp_credentials(host, user, password, database):
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)

        query = """
                    SELECT 
                    smtp_server, 
                    smtp_port, 
                    smtp_username, 
                    smtp_password, 
                    sender_email, 
                    prospect_receiver_emails, 
                    existing_client_receiver_emails, 
                    job_seeker_receiver_emails, 
                    cc_email, 
                    prospect_email_subject, 
                    existing_client_email_subject, 
                    job_seeker_email_subject 
                    FROM 
                    SMTP_CREDENTIALS 
                    LIMIT 1
                """

        cursor.execute(query)

        credentials = cursor.fetchone()

        mydb.close()

        if credentials:
            return {
                "smtp_server": credentials[0],
                "smtp_port": credentials[1],
                "smtp_username": credentials[2],
                "smtp_password": credentials[3],
                "sender_email": credentials[4],
                "prospect_receiver_emails": credentials[5],
                "existing_client_receiver_emails": credentials[6],
                "job_seeker_receiver_emails": credentials[7],
                "cc_email": credentials[8],
                "prospect_email_subject": credentials[9],
                "existing_client_email_subject": credentials[10],
                "job_seeker_email_subject": credentials[11],
            }
        else:
            raise ValueError("No SMTP credentials found in the database.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e, sys)



if __name__ == "__main__":
   
    # create_database(host, user, password)
    # create_tables(host, user, password, database)

    smtp_credentials = get_smtp_credentials(host, user, password, database)
    print(smtp_credentials)
    print(smtp_credentials["job_seeker_receiver_emails"])
    print(type(smtp_credentials["job_seeker_receiver_emails"]))
    print(type(smtp_credentials["cc_email"]))
