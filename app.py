import os
from dotenv import load_dotenv
from flask import Flask

# Load environment variables from .env file
load_dotenv()

# Get the port from the environment variable or default to 5000
PORT = int(os.getenv("PORT", 5000))  # Default to 5000 if PORT is not set

# Flask App Setup
app = Flask(__name__)

@app.route('/')
def index():
    return "NEPSE Live Data is running..."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
