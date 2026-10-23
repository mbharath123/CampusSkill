import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

with open("schema.sql", "r", encoding="utf-8") as file:
    schema = file.read()

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    ssl_disabled=False
)

cursor = connection.cursor()

try:
    for statement in schema.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)

    connection.commit()
    print("CampusSkill schema imported successfully!")

except Exception as error:
    connection.rollback()
    print("Import failed:", error)

finally:
    cursor.close()
    connection.close()
