# need to implement 20.02.2024
def close_mysql_connection(mydb):
    try:
        if mydb.is_connected():
            mydb.close()
            logging.info("MySQL connection closed successfully!")
    except Exception as e:
        logging.error(f"An error occurred while closing the MySQL connection: {e}")
        raise CustomException(e, sys)
    

def close_cursor(cursor):
    try:
        cursor.close()
        logging.info("Cursor closed successfully!")
    except Exception as e:
        logging.error(f"An error occurred while closing the cursor: {e}")
        raise CustomException(e, sys)