import os
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from ftplib import FTP

# FTP Credentials
FTP_HOST = "ftpupload.net"
FTP_USER = "if0_37758998"
FTP_PASS = "VO7kHdsofB1QtS"

# Global HTML content
html_content = ""

# Function to scrape live trading data
def scrape_live_trading_data():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    table_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            table_data.append([
                cells[0].text.strip(),  # SN
                cells[1].text.strip(),  # Symbol
                cells[2].text.strip(),  # LTP
                cells[4].text.strip(),  # Change%
                cells[6].text.strip(),  # Day High
                cells[7].text.strip(),  # Day Low
                cells[8].text.strip(),  # Volume
                cells[9].text.strip()   # Previous Close
            ])
    return table_data

# Function to scrape today's share price summary
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    cells = soup.find_all("td")
    if len(cells) >= 21:
        return {
            "Turnover": cells[10].text.strip(),
            "52_Week_High": cells[19].text.strip(),
            "52_Week_Low": cells[20].text.strip(),
        }
    return {}

# Function to calculate derived values
def calculate_derived_data(data, summary):
    derived_data = []
    for row in data:
        try:
            ltp = float(row[2].replace(",", ""))
            high = float(summary["52_Week_High"].replace(",", ""))
            low = float(summary["52_Week_Low"].replace(",", ""))
            down_from_high = round((high - ltp) / high * 100, 2)
            up_from_low = round((ltp - low) / low * 100, 2)
            derived_data.append({
                "Symbol": row[1],
                "Down_From_High": f"{down_from_high}%",
                "Up_From_Low": f"{up_from_low}%"
            })
        except ValueError:
            continue
    return derived_data

# Function to generate HTML table
def generate_html(data, summary, derived_data):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
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
        <h2>Live Trading Data</h2>
        <table>
            <tr>
                <th>SN</th>
                <th>Symbol</th>
                <th>LTP</th>
                <th>Change%</th>
                <th>Day High</th>
                <th>Day Low</th>
                <th>Previous Close</th>
                <th>Volume</th>
            </tr>
    """
    for row in data:
        html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    
    html += """
        </table>
        <h2>Today's Summary</h2>
        <table>
            <tr><th>Turnover</th><th>52 Week High</th><th>52 Week Low</th></tr>
            <tr>
                <td>{turnover}</td>
                <td>{high}</td>
                <td>{low}</td>
            </tr>
        </table>
        <h2>Derived Data</h2>
        <table>
            <tr><th>Symbol</th><th>Down From High</th><th>Up From Low</th></tr>
    """.format(
        turnover=summary.get("Turnover", "N/A"),
        high=summary.get("52_Week_High", "N/A"),
        low=summary.get("52_Week_Low", "N/A"),
    )
    for row in derived_data:
        html += f"<tr><td>{row['Symbol']}</td><td>{row['Down_From_High']}</td><td>{row['Up_From_Low']}</td></tr>"
    html += """
        </table>
    </body>
    </html>
    """
    return html

# Function to refresh HTML content and upload to FTP server
def refresh_and_upload():
    global html_content
    print("Scraping data...")
    live_data = scrape_live_trading_data()
    summary = scrape_today_share_price()
    derived_data = calculate_derived_data(live_data, summary)
    print("Generating HTML...")
    html_content = generate_html(live_data, summary, derived_data)
    print("Uploading to FTP server...")
    with open("index.html", "w") as file:
        file.write(html_content)
    upload_to_ftp("index.html")
    print("HTML uploaded!")

# Function to upload file to FTP server
def upload_to_ftp(file_path):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        with open(file_path, "rb") as file:
            ftp.storbinary(f"STOR {os.path.basename(file_path)}", file)
        ftp.quit()
        print("File uploaded successfully!")
    except Exception as e:
        print(f"FTP upload failed: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_and_upload, "interval", minutes=5)
scheduler.start()

# Refresh data initially
refresh_and_upload()
