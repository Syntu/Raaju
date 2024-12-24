import os
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Global HTML content
html_content = ""

# Function to scrape today's share price data
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    table_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            table_data.append([cell.text.strip() for cell in cells])
    return table_data

# Function to generate HTML table
def generate_html(table_data):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
                text-align: center;
            }
            td {
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <table>
            <tr>
                <th>Symbol</th>
                <th>LTP</th>
                <th>Change</th>
                <th>High</th>
                <th>Low</th>
                <th>Volume</th>
            </tr>
    """
    for row in table_data:
        html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row[:6]) + "</tr>"
    html += """
        </table>
    </body>
    </html>
    """
    return html

# Function to refresh HTML content
def refresh_html():
    global html_content
    print("Scraping data...")
    table_data = scrape_today_share_price()
    print("Generating HTML...")
    html_content = generate_html(table_data)
    print("HTML updated!")

# Define Flask route
@app.route("/")
def home():
    return html_content or "<h1>Loading data...</h1>"

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_html, "interval", minutes=5)
scheduler.start()

# Refresh data initially
refresh_html()

# Start the server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default port 5000
    app.run(host="0.0.0.0", port=port)
