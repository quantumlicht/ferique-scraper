import os
import shutil
from scraper import FeriqueScraper
from google_writer import GoogleSheetWriter

def lambda_handler(event=None, context=None):
    uname = os.environ['UNAME']
    pwd = os.environ['PWD']
    reer_id = int(os.environ['REER_ACCOUNT_ID'])
    celi_id = int(os.environ['CELI_ACCOUNT_ID'])
    sheet_id = os.environ['SHEET_ID']
    app_name = 'ferique-dumper'
    reer_sheet_namespace = 'reer'
    celi_sheet_namespace = 'celi'
    categories_sheet = 'categories'
    risks_sheet = 'risks'

    cred_file_name = 'sheets.googleapis.com-ferique-scraper.json'

    try:
        os.mkdir('/tmp/.credentials')
    except FileExistsError as e:
        pass
    shutil.copy('./.credentials/{}'.format(cred_file_name), '/tmp/.credentials/{}'.format(cred_file_name))

    scraper = FeriqueScraper(reer_id, celi_id)
    scraper.authenticate(uname, pwd)
    scraper.scrape_account()
    scraper.scrape_categories()
    scraper.scrape_risks()

    writer = GoogleSheetWriter(sheet_id, cred_file_name, app_name)

    # REER
    writer.set_sheet_namespace(reer_sheet_namespace)
    writer.append_formatted(scraper.reer_funds)

    # CELI
    writer.set_sheet_namespace(celi_sheet_namespace)
    writer.append_formatted(scraper.celi_funds)

    #CATEGORIES
    writer.set_sheet_namespace('')
    writer.append_to_sheet(categories_sheet, scraper.reer_categories)
    writer.append_to_sheet(risks_sheet, scraper.reer_risks)

if __name__ == "__main__":
    lambda_handler()
