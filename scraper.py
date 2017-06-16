import requests
import time
import calendar
from bs4 import BeautifulSoup

BASE_URL = "https://client.ferique.com/"
DOM_IDENTIFIER_TEMPLATE = 'pnlAccount_{}'

class FeriqueTable:

    def __init__(self, dom, account_id, offset):
        self.dom = dom
        self.account_id = account_id
        self.__offset = offset
        self.__headers = None
        self.__contents = None
        self.__get_table()

    def __get_table(self):
        self.table = self.__table_by_account_id()
        if self.table is None:
            self.table = self.dom

    def __table_by_account_id(self):
        tables = self.dom.find_all(id=DOM_IDENTIFIER_TEMPLATE.format(self.account_id))
        if len(tables) == 0:
            return None
        else:
            return tables[0]

    def __clean(self, s):
        return s.replace('\xa0', '').replace(',', '.')

    def __clean_rows(self, rows):
        return [[self.__clean(col.string) for col in row.find_all('td') if col.string is not None] for row in rows]

    def __clean_headers(self, headers):
        return [self.__clean(header.string) for header in headers]

    def contents(self):
        if self.__contents is None:
            self.__contents = self.__clean_rows(self.table.tbody.find_all('tr'))
        return self.__contents

    def headers(self, lower_case=False):
        if self.__headers is None:
            self.__headers = self.__clean_headers(self.table.thead.find_all('th'))

        if lower_case:
            return [header.lower() for header in self.__headers]
        else:
            return self.__headers

    def offset(self):
        return self.__offset


class FeriqueScraper:
    def __init__(self, reer_id, celi_id):

        self.url = BASE_URL
        self.cookies = None
        self.reerId = reer_id
        self.celiId = celi_id

        self.__build_endpoint_map()
        self.__set_table_maps()

        self.CELI_CATEGORIES = 'celi_categories'
        self.REER_CATEGORIES = 'reer_categories'
        self.REER_RISKS = 'reer_risks'
        self.CELI_RISKS = 'celi_risks'


        self.ACCOUNTS = 'accounts'
        self.LOGIN = 'login'
        self.celi_funds = []
        self.reer_funds = []
        self.reer_risks = []
        self.celi_risks = []

        self.reer_categories = []
        self.celi_categories = []

    def authenticate(self, uname, pwd):
        payload = {'Username': uname, 'Password': pwd}
        headers = {'Cookie': "lang=fr-CA"}
        login_url = self.__build_url(self.LOGIN)
        r = requests.post(login_url, data=payload, headers=headers)
        self.__request_cookies(r.request)

    def scrape_account(self):
        static_headers = ['Account ID', 'Fond', 'Risque', 'Prix']
        len_static_headers = len(static_headers)
        varying_headers = ['units', 'comptable', 'marchande']

        account_dom = self.__get_dom(self.ACCOUNTS)

        self.reer_funds = FeriqueTable(account_dom, self.reerId, len_static_headers)
        self.celi_funds = FeriqueTable(account_dom, self.celiId, len_static_headers)


    def scrape_categories(self):
        static_headers = ['Catégories d’actif']
        len_static_headers = len(static_headers)
        varying_headers = ['marchande', 'pourcentage']

        reer_categories_dom = self.__get_dom(self.REER_CATEGORIES)
        self.reer_categories = FeriqueTable(reer_categories_dom, self.reerId, len_static_headers)

        celi_categories_dom = self.__get_dom(self.CELI_CATEGORIES)
        self.celi_categories = FeriqueTable(celi_categories_dom, self.celiId, len_static_headers)

    def scrape_risks(self):
        static_headers = ['Risque']
        len_static_headers = len(static_headers)
        varying_headers = ['marchande', 'pourcentage']

        reer_risks_dom = self.__get_dom(self.REER_RISKS)
        self.reer_risks = FeriqueTable(reer_risks_dom, self.reerId, len_static_headers)

        celi_risks_dom = self.__get_dom(self.CELI_RISKS)
        self.celi_risks = FeriqueTable(celi_risks_dom, self.celiId, len_static_headers)

    def __get_dom(self, endpoint):
        url = self.__build_url(endpoint)
        r = requests.get(url, cookies=self.cookies)
        return BeautifulSoup(r.text, 'html.parser')

    def __set_table_maps(self):
        self.title2code = {
            'Code': 'code',
            'Fonds': 'fond',
            'Risque': 'risque',
            'Prix': 'prix',
            'Units': 'unit',
            'Value comptable': 'valeur_comptable',
            'Valeur Marchande': 'valeur_marchande'
        }
        self.code2title = {v: k for k, v in self.title2code.items()}

    def __build_endpoint_map(self):
        reer_fund = "Accounts/Async/Table/funds/{}?".format(self.reerId)
        celi_fund = "Accounts/Async/Table/funds/{}?".format(self.celiId)
        risk_celi = "Accounts/Async/Table/risks/{}?".format(self.celiId)
        risk_reer = "Accounts/Async/Table/risks/{}?".format(self.reerId)
        reer_categories = "Accounts/Async/Table/categories/{}?".format(self.reerId)
        celi_categories = "Accounts/Async/Table/categories/{}?".format(self.celiId)

        self.endpointMap = {
            'accounts': {'endpoint': 'Accounts', 'addTimestamp': False},
            'login': {'endpoint': 'Login', 'addTimestamp': False},
            'reer': {'endpoint': reer_fund, 'addTimestamp': True},
            'celi': {'endpoint': celi_fund, 'addTimestamp': True},
            'celi_risks': {'endpoint': risk_celi, 'addTimestamp': True},
            'reer_risks': {'endpoint': risk_reer, 'addTimestamp': True},
            'celi_categories': {'endpoint': celi_categories, 'addTimestamp': True},
            'reer_categories': {'endpoint': reer_categories, 'addTimestamp': True},
        }

    def __request_cookies(self, req):
        cookie_str = req.headers['cookie']
        self.cookies = dict([tuple(cookie.split('=')) for cookie in cookie_str.split(';')])

    def __build_url(self, endpoint):
        conf = self.endpointMap[endpoint]
        url = self.url + conf['endpoint']
        if conf['addTimestamp']:
            url += "_=" + str(calendar.timegm(time.gmtime()))

        return url