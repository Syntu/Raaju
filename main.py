import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime

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

# Function to scrape today's share price summary
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
                "Turnover": cells[10].text.strip().replace(",", ""),
                "52 Week High": cells[19].text.strip().replace(",", ""),
                "52 Week Low": cells[20].text.strip().replace(",", "")
            })
    return data

# Function to merge live and today's data
def merge_data(live_data, today_data):
    merged = []
    today_dict = {item["Symbol"]: item for item in today_data}
    for live in live_data:
        symbol = live["Symbol"]
        if symbol in today_dict:
            today = today_dict[symbol]
            merged.append({
                "SN": today["SN"],
                "Symbol": symbol,
                "LTP": live["LTP"],
                "Change%": live["Change%"],
                "Day High": live["Day High"],
                "Day Low": live["Day Low"],
                "Previous Close": live["Previous Close"],
                "Volume": live["Volume"],
                "Turnover": today["Turnover"],
                "52 Week High": today["52 Week High"],
                "52 Week Low": today["52 Week Low"],
                "Down From High (%)": f"{((float(today['52 Week High']) - float(live['LTP'])) / float(today['52 Week High']) * 100):.2f}" if today['52 Week High'] != "N/A" else "N/A",
                "Up From Low (%)": f"{((float(live['LTP']) - float(today['52 Week Low'])) / float(today['52 Week Low']) * 100):.2f}" if today['52 Week Low'] != "N/A" else "N/A"
            })
        else:
            # If no match found, use live data with defaults
            merged.append({
                "SN": "-",
                "Symbol": symbol,
                "LTP": live["LTP"],
                "Change%": live["Change%"],
                "Day High": live["Day High"],
                "Day Low": live["Day Low"],
                "Previous Close": live["Previous Close"],
                "Volume": live["Volume"],
                "Turnover": "N/A",
                "52 Week High": "N/A",
                "52 Week Low": "N/A",
                "Down From High (%)": "N/A",
                "Up From Low (%)": "N/A"
            })
    return merged

# Function to generate HTML
def generate_html(data):
    updated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            body {{font-family: Arial, sans-serif; margin: 20px;}}
            table {{width: 100%; border-collapse: collapse; margin-top: 20px;}}
            th, td {{border: 1px solid #ddd; padding: 8px; text-align: center;}}
            th {{background-color: #8B4513; color: white; cursor: pointer; position: sticky; top: 0;}}
            tr:hover {{background-color: #f1f1f1;}}
            td {{cursor: pointer;}}
            .header {{text-align: center; font-weight: bold; font-size: 24px; margin-bottom: 20px;}}
            .welcome {{text-align: center; font-size: 18px; margin-top: 40px;}}
            .footer {{display: flex; justify-content: space-between; margin-top: 20px; font-size: 14px;}}
            .footer a {{text-decoration: none; color: #8B4513; font-weight: bold;}}
            .highlight {{background-color: #ffff99 !important;}}
            .light-red {{background-color: #FFCCCB;}}
            .light-green {{background-color: #D4EDDA;}}
            .light-blue {{background-color: #CCE5FF;}}
        </style>
        <script>
            // Row highlight function
            function highlightRow(row) {{
                var rows = document.getElementsByTagName("tr");
                for (var i = 0; i < rows.length; i++) {{
                    rows[i].classList.remove("highlight");
                }}
                row.classList.add("highlight");
            }}
        </script>
    </head>
    <body>
        <div class="header">NEPSE Live Data</div>
        <table id="dataTable">
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
                    <th>Down From High (%)</th>
                    <th>Up From Low (%)</th>
                </tr>
            </thead>
            <tbody>
    """
    for row in data:
        change_class = "light-red" if float(row["Change%"]) < 0 else (
            "light-green" if float(row["Change%"]) > 0 else "light-blue")
        html += f"""
            <tr onclick="highlightRow(this)">
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
                <td>{row["Down From High (%)"]}</td>
                <td>{row["Up From Low (%)"]}</td>
            </tr>
        """
    html += f"""
            </tbody>
        </table>
        <div class="welcome">Welcome 🙏 to NEPSE data Website.</div>
        <div class="footer">
            <div>Updated on: {updated_time}</div>
            <div><a href="https://www.facebook.com/srajghimire" target="_blank">Developed By : Syntoo</a></div>
        </div>
    </body>
    </html>
    """
    return html

# Function to upload the HTML to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh data function
def refresh_data():
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    html_content = generate_html(merged_data)
    upload_to_ftp(html_content)

# Schedule the data refresh
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial refresh
refresh_data()

# Keep running
try:
    while True:
        pass
except KeyboardInterrupt:
    scheduler.shutdown()
