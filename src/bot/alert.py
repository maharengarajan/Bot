import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import ssl
import sys
from src.bot.exception import CustomException
from src.bot.logger import logging
from src.bot.database import get_smtp_credentials

def configure():
    load_dotenv()

configure()
host = os.getenv("database_host_name")
user = os.getenv("database_user_name")
password = os.getenv("database_user_password")
database = os.getenv("database_name")



def send_email(sender_email, receiver_emails, cc_email, subject, message, from_name="Chatbot_Datanetiix"):
    # Ensure receiver_emails is treated as a list
    if isinstance(receiver_emails, str):
        receiver_emails = [receiver_emails]

    # Ensure cc_email is treated as a list
    if isinstance(cc_email, str):
        cc_email = [cc_email]

    # Create a multipart message container
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{sender_email}>"
    msg["To"] = ", ".join(receiver_emails)
    msg["Cc"] = ", ".join(cc_email)
    msg["Subject"] = subject

    # Add the message body
    msg.attach(MIMEText(message, "plain"))

    try:
        smtp_credentials = get_smtp_credentials(host, user, password, database)
        logging.info(f"SMTP credentials fetched: {smtp_credentials}")

        # Debugging: Print receiver_emails and cc_email
        logging.info(f"Receiver Emails (Processed): {receiver_emails}")
        logging.info(f"CC Emails (Processed): {cc_email}")

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Create a secure connection with the SMTP server
        server = smtplib.SMTP(smtp_credentials['smtp_server'], smtp_credentials['smtp_port'])
        server.starttls(context=context)
        server.login(smtp_credentials['smtp_username'], smtp_credentials['smtp_password'])

        # Send the email
        all_recipients = receiver_emails + cc_email
        logging.info(f"Sending email to: {all_recipients}")

        server.sendmail(sender_email, all_recipients, msg.as_string())
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"An error occurred while sending the email: {str(e)}")
        raise CustomException(e, sys)
    finally:
        # Close the SMTP connection
        logging.info("Closing the SMTP connection")
        server.quit()


if __name__=="__main__":
    smtp_credentials = get_smtp_credentials(host, user, password, database)
    send_email(smtp_credentials['sender_email'], smtp_credentials['prospect_receiver_emails'], smtp_credentials['cc_email'], smtp_credentials['prospect_email_subject'], message='test', from_name="Chatbot_Datanetiix")