from flask import Flask
from app.scheduler import start_scheduler
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Environment variables
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

# Start Scheduler
start_scheduler(FTP_HOST, FTP_USER, FTP_PASS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))