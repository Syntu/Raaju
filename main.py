import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

# Function to scrape live trading data
def scrape_live_trading():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    live_data = {}
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            symbol = cells[1].text.strip()
            live_data[symbol] = {
                "LTP": cells[2].text.strip(),
                "Change%": cells[4].text.strip(),
                "Day High": cells[6].text.strip(),
                "Day Low": cells[7].text.strip(),
                "Previous Close": cells[9].text.strip(),
                "Volume": cells[8].text.strip(),
            }
    return live_data

# Function to scrape today's share price data
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    today_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            today_data.append({
                "SN": cells[0].text.strip(),
                "Symbol": cells[1].text.strip(),
                "Turnover": cells[10].text.strip(),
                "52 Week High": cells[19].text.strip(),
                "52 Week Low": cells[20].text.strip(),
            })
    return today_data

# Function to merge data based on Symbol
def merge_data(today_data, live_data):
    merged_data = []
    for row in today_data:
        symbol = row["Symbol"]
        if symbol in live_data:
            merged_data.append({
                "SN": row["SN"],
                "Symbol": symbol,
                **live_data[symbol],
                "Turnover": row["Turnover"],
                "52 Week High": row["52 Week High"],
                "52 Week Low": row["52 Week Low"],
            })
        else:
            # Use Today's Share Price data if not found in Live Trading
            merged_data.append({
                "SN": row["SN"],
                "Symbol": symbol,
                "LTP": "N/A",
                "Change%": "N/A",
                "Day High": "N/A",
                "Day Low": "N/A",
                "Previous Close": "N/A",
                "Volume": "N/A",
                "Turnover": row["Turnover"],
                "52 Week High": row["52 Week High"],
                "52 Week Low": row["52 Week Low"],
            })
    return merged_data

# Function to generate HTML table
def generate_html(merged_data):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
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
            .positive { background-color: lightgreen; }
            .negative { background-color: lightcoral; }
            .neutral { background-color: lightblue; }
            .table-container {
                max-height: 80vh;
                overflow: auto;
            }
            h1 {
                text-align: center;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <div class="table-container">
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
    for row in merged_data:
        change_class = "neutral"
        if row["Change%"] != "N/A":
            change = float(row["Change%"].replace("%", "").replace(",", ""))
            if change > 0:
                change_class = "positive"
            elif change < 0:
                change_class = "negative"

        html += f"""
        <tr>
            <td>{row["SN"]}</td>
            <td>{row["Symbol"]}</td>
            <td>{row["LTP"]}</td>
            <td class="{change_class}">{row["Change%"]}</td>
            <td>{row["Day High"]}</td>
            <td>{row["Day Low"]}</td>
            <td>{row["Previous Close"]}</td>
            <td>{row["Volume"]}</td>
            <td>{row["Turnover"]}</td>
            <td>{row["52 Week High"]}</td>
            <td>{row["52 Week Low"]}</td>
        </tr>
        """
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html

# Function to upload HTML to FTP server
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")  # Change to the correct directory if necessary
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Function to refresh data
def refresh_data():
    print("Fetching data...")
    today_data = scrape_today_share_price()
    live_data = scrape_live_trading()
    merged_data = merge_data(today_data, live_data)
    print("Generating HTML...")
    html_content = generate_html(merged_data)
    print("Uploading to FTP...")
    upload_to_ftp(html_content)
    print("Data refreshed and uploaded successfully!")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=5)
scheduler.start()

# Refresh data initially
refresh_data()

# Keep the script running
try:
    print("Script running... Press Ctrl+C to stop.")
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    print("Stopping script...")
    scheduler.shutdown()
