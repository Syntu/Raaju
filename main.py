import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to fetch data from NEPSEalpha
def fetch_nepsealpha_data():
    url = "https://nepsealpha.com/live-market"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    data = {
        "date": soup.select_one('td:contains("Date") + td').text.strip(),
        "current": soup.select_one('td:contains("Current") + td').text.strip(),
        "daily_gain": soup.select_one('td:contains("Daily Gain") + td').text.strip(),
        "turnover": soup.select_one('td:contains("Turnover") + td').text.strip(),
        "previous_close": soup.select_one('td:contains("Previous Close") + td').text.strip(),
        "positive_stocks": soup.select_one('td:contains("Positive Stocks") + td').text.strip(),
        "neutral_stocks": soup.select_one('td:contains("Neutral Stocks") + td').text.strip(),
        "negative_stocks": soup.select_one('td:contains("Negative Stocks") + td').text.strip(),
        "total_turnover": soup.select_one('td:contains("Total Turnover Rs:") + td').text.strip(),
        "total_traded_shares": soup.select_one('td:contains("Total Traded Shares") + td').text.strip(),
        "total_transactions": soup.select_one('td:contains("Total Transactions") + td').text.strip(),
        "total_scrips_traded": soup.select_one('td:contains("Total Scrips Traded") + td').text.strip(),
        "total_float_market_cap": soup.select_one('td:contains("Total Float Market Capitalization Rs:") + td').text.strip(),
        "nepse_market_cap": soup.select_one('td:contains("NEPSE Market Cap") + td').text.strip(),
    }
    return data

# Function to generate HTML
def generate_html(data):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Data</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
    <div class="col-md-4">
        <div class="card mt-2">
            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0" id="nepse-table">
                    <tbody>
                        <tr>
                            <td colspan="2" class="bg-primary text-white text-bold">
                                <select class="form-control">
                                    <option value="NEPSE">NEPSE</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Date</td>
                            <td id="date">{data['date']}</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Current</td>
                            <td id="current">{data['current']}</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold line-1-3">Daily Gain</td>
                            <td id="daily-gain">{data['daily_gain']}</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Turnover</td>
                            <td id="turnover">{data['turnover']}</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Previous Close</td>
                            <td id="previous-close">{data['previous_close']}</td>
                        </tr>
                        <tr class="bg-secondary text-white large text-bold">
                            <td colspan="2">Market Sentiment</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Positive Stocks</td>
                            <td id="positive-stocks">{data['positive_stocks']}</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Neutral Stocks</td>
                            <td id="neutral-stocks">{data['neutral_stocks']}</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Negative Stocks</td>
                            <td id="negative-stocks">{data['negative_stocks']}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="mt-3">
            <h5 class="box_header">Market Summary</h5>
            <div class="card">
                <div class="card-body p-0 table-responsive">
                    <table class="table table-hover table-striped table-bordered mb-0">
                        <tbody>
                            <tr>
                                <th class="font-weight-bold">Total Turnover Rs:</th>
                                <td id="total-turnover">{data['total_turnover']}</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Traded Shares</th>
                                <td id="total-traded-shares">{data['total_traded_shares']}</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Transactions</th>
                                <td id="total-transactions">{data['total_transactions']}</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Scrips Traded</th>
                                <td id="total-scrips-traded">{data['total_scrips_traded']}</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Float Market Capitalization Rs:</th>
                                <td id="total-float-market-cap">{data['total_float_market_cap']}</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">NEPSE Market Cap</th>
                                <td id="nepse-market-cap">{data['nepse_market_cap']}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    """
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh Data
def refresh_data():
    data = fetch_nepsealpha_data()
    html_content = generate_html(data)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
