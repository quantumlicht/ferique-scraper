### Ferique Scraper
Scraper for ferique.com portal

### Requirements
- python 3.6
- dependencies listed in `requirements.txt`
-  a valid `.credentials/sheets.googleapis.com-ferique-scraper.json` file. This can be obtained in GCP by registering an app and getting a token 

### Installation
`pip install requirements.txt`

### Execution
This script is meant to be run in a AWS lambda function, but can be run locally by invoking with `python lambda_function.py`

### Package for lambda execution
Run `python build.py` to create a zip archive that can be uploaded to AWS to be run. It could also be stored to S3.