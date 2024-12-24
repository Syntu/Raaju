import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

app = Flask(__name__)

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
                "LTP": cells[2].text.strip(),
                "Change%": cells[4].text.strip(),
                "Day High": cells[6].text.strip(),
                "Day Low": cells[7].text.strip(),
                "Previous Close": cells[9].text.strip(),
                "Volume": cells[8].text.strip()
            })
    return data

# Function to scrape today's share price data
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            data.append({
                "SN": cells[0].text.strip(),
                "Symbol": cells[1].text.strip(),
                "Turnover": cells[10].text.strip(),
                "52 Week High": cells[19].text.strip(),
                "52 Week Low": cells[20].text.strip()
            })
    return data

# Merge data based on Symbol
def merge_data(today_data, live_data):
    merged_data = []
    for today in today_data:
        symbol = today["Symbol"]
        matching_live_data = next((item for item in live_data if item["Symbol"] == symbol), None)
        if matching_live_data:
            merged_data.append({**today, **matching_live_data})
        else:
            merged_data.append(today)  # If no match, use today's data only
    return merged_data

# Function to generate HTML table
def generate_html(data):
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
                background-color: brown;
                color: white;
                position: sticky;
                top: 0;
                z-index: 1;
            }
            td {
                text-align: center;
            }
            .negative {
                background-color: lightcoral;
            }
            .positive {
                background-color: lightgreen;
            }
            .neutral {
                background-color: lightblue;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <table>
            <thead>
                <tr>
                    <th>SN</th>
                    <th>Symbol</th>
                    <th>LTP</th>
                    <th>Change%</th>
                    <th>Day High</th>
                    <th>Day Low</th>
                    <th>Previous Close</th>
                    <th>Volume</th>
                    <th>Turnover</th>
                    <th>52 Week High</th>
                    <th>52 Week Low</th>
                </tr>
            </thead>
            <tbody>
    """
    for row in data:
        change_class = "neutral"
        if row.get("Change%"):
            try:
                change = float(row["Change%"].replace("%", ""))
                if change > 0:
                    change_class = "positive"
                elif change < 0:
                    change_class = "negative"
            except ValueError:
                pass
        html += f"""
            <tr>
                <td>{row.get('SN', '')}</td>
                <td>{row.get('Symbol', '')}</td>
                <td>{row.get('LTP', '')}</td>
                <td class="{change_class}">{row.get('Change%', '')}</td>
                <td>{row.get('Day High', '')}</td>
                <td>{row.get('Day Low', '')}</td>
                <td>{row.get('Previous Close', '')}</td>
                <td>{row.get('Volume', '')}</td>
                <td>{row.get('Turnover', '')}</td>
                <td>{row.get('52 Week High', '')}</td>
                <td>{row.get('52 Week Low', '')}</td>
            </tr>
        """
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

# Upload HTML to FTP server
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")  # Change to correct directory if needed
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh data
def refresh_data():
    today_data = scrape_today_share_price()
    live_data = scrape_live_trading()
    merged_data = merge_data(today_data, live_data)
    html_content = generate_html(merged_data)
    upload_to_ftp(html_content)

# Schedule data refresh
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=5)
scheduler.start()

@app.route("/")
def home():
    return "<h1>NEPSE Data Sync is Active</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    refresh_data()  # Initial refresh
    app.run(host="0.0.0.0", port=port)
