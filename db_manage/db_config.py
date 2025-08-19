import mysql.connector

config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'Student_db'
}

def get_connection():
    return mysql.connector.connect(**config)