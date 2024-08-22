import sys
import os
from dotenv import load_dotenv
from src.bot.exception import CustomException
from src.bot.logger import logging
from src.bot.database import connect_to_mysql_database, create_cursor_object


def configure():
    load_dotenv()


configure()
host = os.getenv("database_host_name")
user = os.getenv("database_user_name")
password = os.getenv("database_user_password")
database = os.getenv("database_name")


def smtp_creds_to_db(host, user, password, database):
    try:
        mydb = connect_to_mysql_database(host, user, password, database)
        cursor = create_cursor_object(mydb)

        table_queries = """
                            CREATE TABLE IF NOT EXISTS SMTP_CREDENTIALS(
                            SID INT AUTO_INCREMENT PRIMARY KEY,
                            smtp_server VARCHAR(255),
                            smtp_port INT,
                            smtp_username VARCHAR(255),
                            smtp_password VARCHAR(255),
                            sender_email VARCHAR(255),
                            prospect_receiver_emails TEXT,
                            existing_client_receiver_emails TEXT,
                            job_seeker_receiver_emails TEXT,
                            cc_email TEXT,
                            prospect_email_subject VARCHAR(255),
                            existing_client_email_subject VARCHAR(255),
                            job_seeker_email_subject VARCHAR(255)
                        )
                        """
        insert_values_query = """
                            INSERT INTO SMTP_CREDENTIALS (
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
                            )  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
        values = (
            "smtp.office365.com",
            587,
            "customappsmtp@datanetiix.com",
            "Vom71445",
            "customappsmtp@datanetiix.com",
            "rengarajan@datanetiix.com,aiengineer@datanetiix.com",
            "rengarajan@datanetiix.com,aiengineer@datanetiix.com",
            "rengarajan@datanetiix.com,aiengineer@datanetiix.com",
            "rengarajan@datanetiix.com",
            "Chatbot - Prospect conversation",
            "Chatbot - Existing client conversation",
            "Chatbot - Job Seeker conversation",
        )

        # Execute table creation queries
        cursor.execute(table_queries)
        cursor.execute(insert_values_query, values)
        mydb.commit()
        logging.info("SMTP Tables and columns created successfully")
        return True
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e, sys)


if __name__ == "__main__":
    smtp_creds_to_db(host, user, password, database)
