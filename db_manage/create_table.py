import mysql.connector
from db_config import get_connection

with open('schema/Alter_table.sql', 'r') as file:
    sql_script = file.read()

conn = get_connection()
cursor = conn.cursor()

for command in sql_script.strip().split(';'):
    if command.strip():  
        cursor.execute(command)

conn.commit()
cursor.close()
conn.close()

print("Database schema created successfully.")