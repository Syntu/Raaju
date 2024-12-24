import os
import requests
from ftplib import FTP
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve Telegram Bot Token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_PATH = os.getenv("FTP_PATH", "/public_html/")

if not all([BOT_TOKEN, FTP_HOST, FTP_USER, FTP_PASS]):
    raise ValueError("Missing required environment variables")

# Global Data Storage (refresh location)
latest_data = {
    "symbol_data": {},
    "general_data": {}
}

# Scrape Sharesansar Data for Specific Symbol
def scrape_symbol_data(symbol_name):
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    stock_data = []
    for row in rows:
        cells = row.find_all("td")
        if cells and len(cells) > 8:  # Ensure valid row structure
            data = {
                "Symbol": cells[1].text.strip(),
                "LTP": cells[2].text.strip(),
                "Change Percent": cells[4].text.strip(),
                "Day High": cells[6].text.strip(),
                "Day Low": cells[7].text.strip(),
                "Volume": cells[8].text.strip(),
            }
            stock_data.append(data)
    return stock_data

# Scrape Today's Share Price Summary
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table_data = soup.find_all("td")
    data = {
        "Turn Over": table_data[10].text.strip(),
        "52 Week High": table_data[19].text.strip(),
        "52 Week Low": table_data[20].text.strip(),
    }
    return data

# Function to Generate and Upload index.html
def update_index_html():
    try:
        # Fetch and process the stock data
        stock_data = scrape_symbol_data("symbol_name")  # Replace with actual symbol or loop through multiple
        general_data = scrape_today_share_price()

        # Create HTML content with a table
        html_content = f"""
        <html>
        <head>
            <title>Stock Market Update</title>
            <style>
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                table, th, td {{
                    border: 1px solid black;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <h1>Latest Stock Data</h1>
            <h2>Stock Data:</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>LTP</th>
                        <th>Change Percent</th>
                        <th>Day High</th>
                        <th>Day Low</th>
                        <th>Volume</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add stock data rows to the table
        for stock in stock_data:
            html_content += f"""
                <tr>
                    <td>{stock['Symbol']}</td>
                    <td>{stock['LTP']}</td>
                    <td>{stock['Change Percent']}</td>
                    <td>{stock['Day High']}</td>
                    <td>{stock['Day Low']}</td>
                    <td>{stock['Volume']}</td>
                </tr>
            """
        
        # Add general data to the HTML
        html_content += f"""
                </tbody>
            </table>
            <h2>General Market Data:</h2>
            <p>Turn Over: {general_data.get('Turn Over', 'N/A')}</p>
            <p>52 Week High: {general_data.get('52 Week High', 'N/A')}</p>
            <p>52 Week Low: {general_data.get('52 Week Low', 'N/A')}</p>
        </body>
        </html>
        """

        # Connect to FTP server
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        # Upload the HTML file to the server
        with open("index.html", "w") as file:
            file.write(html_content)

        with open("index.html", "rb") as file:
            ftp.storbinary(f"STOR {FTP_PATH}index.html", file)

        print("index.html updated successfully on InfinityFree!")
        ftp.quit()
    except Exception as e:
        print(f"Error updating index.html: {e}")

# Scheduler to update every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(update_index_html, "interval", minutes=5)
scheduler.start()

# Initial update
update_index_html()

# Start Polling
if __name__ == "__main__":
    print("Bot and scheduler are running...")
    while True:
        pass  # Keep the script running