import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template_string

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to fetch NEPSE data
def fetch_nepse_data():
    url = "https://www.nepalipaisa.com/live-market"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            nepse_data = soup.find('div', class_='market-header').text.strip()
            return nepse_data
        except AttributeError:
            return "Error: Could not find NEPSE data. The website structure may have changed."
    else:
        return f"Error: Failed to fetch data. Status code: {response.status_code}"

# Function to scrape live trading data
def scrape_live_trading():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            data.append({
                "Symbol": cells[1].text.strip(),
                "LTP": cells[2].text.strip().replace(",", ""),
                "Change%": cells[4].text.strip(),
                "Day High": cells[6].text.strip().replace(",", ""),
                "Day Low": cells[7].text.strip().replace(",", ""),
                "Previous Close": cells[9].text.strip().replace(",", ""),
                "Volume": cells[8].text.strip().replace(",", "")
            })
    return data

# Function to generate HTML
def generate_html(main_table, nepse_index):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            h1 {{
                text-align: center;
                font-size: 40px;
                font-weight: bold;
                margin-top: 20px;
            }}
            h2 {{
                text-align: center;
                font-size: 18px;
                margin-bottom: 20px;
            }}
            .nepse-index {{
                text-align: center;
                font-size: 24px;
                font-weight: bold;
                color: #ff5733;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 14px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #8B4513;
                color: white;
            }}
        </style>
    </head>
    <body>
        <h1>NEPSE Data Table</h1>
        <h2>Welcome to NEPSE Stock Data</h2>
        <div class="nepse-index">
            {nepse_index}
        </div>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>LTP</th>
                    <th>Change%</th>
                    <th>Day High</th>
                    <th>Day Low</th>
                </tr>
            </thead>
            <tbody>
    """
    for row in main_table:
        html += f"""
        <tr>
            <td>{row['Symbol']}</td>
            <td>{row['LTP']}</td>
            <td>{row['Change%']}</td>
            <td>{row['Day High']}</td>
            <td>{row['Day Low']}</td>
        </tr>
        """
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

# Refresh Data
def refresh_data():
    nepse_index = fetch_nepse_data()
    live_data = scrape_live_trading()
    html_content = generate_html(live_data, nepse_index)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
