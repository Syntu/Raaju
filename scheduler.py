from apscheduler.schedulers.background import BackgroundScheduler
from utils.scraper import scrape_live_trading, scrape_today_share_price
from utils.html_generator import generate_html
from utils.ftp_uploader import upload_to_ftp

def refresh_data(ftp_host, ftp_user, ftp_pass):
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    html_content = generate_html(live_data + today_data)  # Combine data
    upload_to_ftp(ftp_host, ftp_user, ftp_pass, html_content)

def start_scheduler(ftp_host, ftp_user, ftp_pass):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: refresh_data(ftp_host, ftp_user, ftp_pass), "interval", minutes=5)
    scheduler.start()