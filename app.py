from flask import Flask

# Flask App Setup
app = Flask(__name__)

@app.route('/')
def index():
    return "NEPSE Live Data is running..."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)