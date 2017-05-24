import httplib2
import os

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import discovery
from datetime import datetime
from transform import Transform


class GoogleSheetWriter:

    def __init__(self, sheet_id, credential_file_name, app_name):
        self.CLIENT_SECRET_FILE = 'client_secret.json'
        self.SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

        # TODO move to env variable params
        self.application_name = app_name

        self.credential_file_name = credential_file_name
        self.sheet_id = sheet_id
        self.namespace = None
        self.sheet_name = None
        self.__configure_flags()
        self.__authenticate()
        self.__build_service()
        self.ROW_DIR = 'A'
        self.COL_DIR = 1

    def __configure_flags(self):
        try:
            import argparse
            self.flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            self.flags = None

    def __build_service(self):
        http = self.credentials.authorize(httplib2.Http())
        discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                         'version=v4')
        service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discovery_url)
        self.sheet_values_service = service.spreadsheets().values()

    def __authenticate(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        # home_dir = os.path.expanduser('~')
        # credential_dir = '/tmp/.credentials'
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, self.credential_file_name)
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.application_name
            if self.flags:
                credentials = tools.run_flow(flow, store, self.flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        self.credentials = credentials

    def __configure_sheet(self):
        self.next_col_id = self.available_range_id(self.COL_DIR)
        self.next_row = self.available_range_id(self.ROW_DIR) + 1  # rows are 1-based

    @staticmethod
    def id_2_col(id_, start='A'):
        return chr(ord(start) + id_)

    def set_sheet_namespace(self, namespace):
        self.namespace = namespace

    def __set_sheet_name(self, sheet_name):
        self.sheet_name = sheet_name
        self.__configure_sheet()

    # Get next available free cell index in a given direction (row or column)
    def available_range_id(self, direction):
        range_ = self.ns_range(direction, direction)
        req = self.sheet_values_service.get(spreadsheetId=self.sheet_id, range=range_)
        res = req.execute()

        if 'values' not in res:
            range_id = 0
        else:
            if res['majorDimension'] == 'ROWS':
                range_id = len(res['values'])
            else:
                range_id = len(res['values'][0])
        return range_id

    def is_headers_set(self, headers):
        range_ = self.ns_range('A', 'A')
        req = self.sheet_values_service.get(spreadsheetId=self.sheet_id, range=range_)
        res = req.execute()
        return 'values' in res and res['values'][0][0] == headers[0]

    def ns_range(self, start, end):
        if self.namespace is None:
            raise Exception("Undefined sheet namespace")

        if self.sheet_name is None:
            raise Exception("Undefined sheet name")

        if self.namespace == '':
            return "{}!{}:{}".format(self.sheet_name, start, end)
        else:
            return "'{}-{}'!{}:{}".format(self.namespace, self.sheet_name, start, end)

    def range_from_data(self, formatted_data, row_start=1, col_start=0):
        start_row = row_start  # offset for col header
        col = self.__class__.id_2_col(col_start)
        range_start = col + str(start_row)

        end_row = start_row + len(formatted_data)
        range_end = self.__class__.id_2_col(len(formatted_data[0]), col) + str(end_row)

        return self.ns_range(range_start, range_end)

    def __set_static_headers(self, table_data, offset):
        headers = table_data.headers()[:offset]
        transposed_headers = Transform.transpose2d([headers])
        range_ = self.range_from_data(transposed_headers)
        self.update_range(transposed_headers, range_)

    def __set_varying_headers(self, table_data, offset):
        headers = table_data.headers()[offset:]
        # TODO: Make sure we are putting data in correct account using row_headers to match with accountId
        varying_headers = [datetime.now().strftime("%x %X")]
        transposed_headers = Transform.transpose2d([varying_headers])
        row_offset = offset + 1 if offset > self.next_row else self.next_row
        range_ = self.range_from_data(transposed_headers, row_start=row_offset)
        self.update_range(transposed_headers, range_)

    def __set_static_data(self, arr_data):
        tranposed_data = Transform.transpose2d(arr_data)
        range_ = self.range_from_data(tranposed_data, col_start=1)
        self.update_range(tranposed_data, range_)

    def __set_varying_data(self, arr_data, offset):
        tranposed_data = Transform.transpose2d(arr_data)
        row_offset = offset+1 if offset > self.next_row else self.next_row
        range_ = self.range_from_data(tranposed_data, row_start=row_offset, col_start=1)
        self.update_range(tranposed_data, range_)

    # table_content data has a headers_method
    def append_formatted(self, table_data):
        # TODO: Build static_data and varying_data methods
        offset = table_data.offset()
        varying_headers = table_data.headers()[offset:]
        for i, header in enumerate(varying_headers):
            self.__set_sheet_name(header)
            if not self.is_headers_set(table_data.headers()):
                self.__set_static_headers(table_data, offset)
                self.__set_static_data([data[:offset] for data in table_data.contents()])
            self.__set_varying_headers(table_data, offset)
            self.__set_varying_data([[data[i + offset]] for data in table_data.contents()], offset)

    def append_to_sheet(self, sheet_name, table_data):
        self.__set_sheet_name(sheet_name)

        offset = table_data.offset()
        if not self.is_headers_set(table_data.headers()):
            self.__set_static_headers(table_data, offset)
            self.__set_static_data([data[:offset] for data in table_data.contents()])
        self.__set_varying_headers(table_data, offset)
        self.__set_varying_data([[data[offset:][0]] for data in table_data.contents()], offset)

    def update_range(self, data, range_):
        value_range_body = {'values': data}
        return self.sheet_values_service.update(spreadsheetId=self.sheet_id, range=range_,
                                                valueInputOption='USER_ENTERED', body=value_range_body).execute()
