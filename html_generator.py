from datetime import datetime
from pytz import timezone

def generate_html(main_table):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<html>...HTML content here...</html>"""  # Paste your HTML content
    return html