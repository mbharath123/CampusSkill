
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_disabled=False
    )

    print("Aiven MySQL connection successful!")

    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    print("Connected database:", cursor.fetchone()[0])

    cursor.close()
    connection.close()

except Exception as error:
    print("Connection failed:", error)
