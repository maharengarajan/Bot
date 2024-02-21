from datetime import datetime, timezone
from src.logger import logging
from src.exception import CustomException
import sys
from dotenv import load_dotenv
import re


def configure():
    load_dotenv()

def get_current_utc_datetime():
    try:
        current_utc_datetime = datetime.now(timezone.utc)
        logging.info("current date time collected successfully")
        return current_utc_datetime
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)


def extract_utc_date_and_time(utc_datetime):
    try:
        utc_date = utc_datetime.strftime('%Y-%m-%d')
        utc_time = utc_datetime.strftime('%H:%M:%S')
        logging.info("UTC date and UTC time colleceted")
        return utc_date, utc_time
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise CustomException(e,sys)
    

def is_valid_name(name):
    return bool(re.match(r"^[A-Za-z\s]+$", name.strip()))


def is_valid_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def is_valid_contact_number(contact):
    return bool(re.match(r"^\+?\d{1,3}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$",contact,))
    

    

# print(get_current_utc_datetime())
# print(extract_utc_date_and_time(get_current_utc_datetime()))
# print(type(extract_utc_date_and_time(get_current_utc_datetime())))