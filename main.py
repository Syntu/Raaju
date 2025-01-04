import os
import requests
import ftplib
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

def fetch_nepse_indices():
    url = "https://sharehubnepal.com/nepse/indices"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    # Send request to the website
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch the webpage. Status Code: {response.status_code}")
        return []

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table
    table = soup.find('table', {'class': 'min-w-max w-full caption-bottom border-collapse'})
    if not table:
        print("Table not found. Verify the table class.")
        return []

    # Extract data from the table
    indices_data = []
    rows = table.find('tbody').find_all('tr')  # Locate all rows inside <tbody>
    for row in rows:
        columns = row.find_all('td')
        if len(columns) >= 6:  # Ensure there are enough columns
            indices = columns[0].text.strip()
            value = columns[1].text.strip()
            ch = columns[2].text.strip()
            ch_percent = columns[3].text.strip()
            high = columns[4].text.strip()
            low = columns[5].text.strip()

            indices_data.append({
                "Indices": indices,
                "Value": value,
                "Ch": ch,
                "Ch%": ch_percent,
                "HIGH": high if high != "N/A" else None,
                "LOW": low if low != "N/A" else None
            })

    return indices_data

def save_to_html(data):
    # HTML structure
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Indices</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 1em;
                text-align: left;
            }
            th, td {
                padding: 12px 15px;
                border: 1px solid #ddd;
            }
            th {
                background-color: #f4f4f4;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Indices</h1>
        <table>
            <thead>
                <tr>
                    <th>Indices</th>
                    <th>Value</th>
                    <th>Ch</th>
                    <th>Ch%</th>
                    <th>High</th>
                    <th>Low</th>
                </tr>
            </thead>
            <tbody>
    """

    # Add data to HTML table
    for item in data:
        html_content += f"""
        <tr>
            <td>{item['Indices']}</td>
            <td>{item['Value']}</td>
            <td>{item['Ch']}</td>
            <td>{item['Ch%']}</td>
            <td>{item['HIGH'] if item['HIGH'] else 'N/A'}</td>
            <td>{item['LOW'] if item['LOW'] else 'N/A'}</td>
        </tr>
        """

    # Close HTML structure
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    # Save HTML to a file
    with open('nepse_indices.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

    print("HTML file has been saved as 'nepse_indices.html'.")
    return 'nepse_indices.html'

def upload_to_ftp(file_path):
    try:
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")  # Change directory to target folder
            with open(file_path, "rb") as file:
                ftp.storbinary(f"STOR index.html", file)
        print("File successfully uploaded to FTP.")
    except Exception as e:
        print(f"Failed to upload file to FTP: {str(e)}")

# Fetch data
data = fetch_nepse_indices()

# Save data to HTML and upload to FTP
if data:
    html_file = save_to_html(data)
    upload_to_ftp(html_file)
else:
    print("No data fetched to save or upload.")
