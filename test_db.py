import os
import psycopg2
from dotenv import load_dotenv

# Load your .env file
load_dotenv()

print("Attempting to connect...")

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5
    )
    print("✅ SUCCESS! Your password and credentials are 100% correct.")
    conn.close()
except Exception as e:
    print("❌ FAILED! The connection was rejected.")
    print(f"Error Details: {e}")