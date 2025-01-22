from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC

"""
This is a requests module only implementation. To be used on iphone or other devices that can't support the api
version.

Note that the api version must be run to create the necessary authentication documents (this file does not implement
a robust oauth method). It relies on a refresh token that is created by the TdApi library, which is valid for 90 days.
The TdApi also updates the refresh token when necessary.
"""


class TdRequests:
    def __init__(self, add_api_delay=True):
        self.api_delay = add_api_delay
        self.consumer_key = ""              # Key for app
        self.refresh_token = ""             # Token that is valid for 90 days, used to create session token
        self.auth_header = ""            # Create session token active for 30 mins

        self._get_keys_and_tokens()
        self._get_session_header()

    def _get_keys_and_tokens(self):
        self.refresh_token = fC.load_json_from_file(
            osC.create_file_path_string(
                ['resources', 'commonStocks', 'keys', 'td_token_path.json'])
        )["token"]["refresh_token"]

        self.consumer_key = fC.read_single_line_from_file(
            osC.create_file_path_string(['resources', 'commonStocks', 'keys', 'td_consumer_key.txt'])
        )


    def _get_session_header(self):
        """
        :return:
        """
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.consumer_key
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        auth_response = rC.use_requests_return_json("https://api.tdameritrade.com/v1/oauth2/token",
                                                    request_type="POST", headers=headers, params=params)
        self.auth_header = {"Authorization": "Bearer " + auth_response["access_token"]}


    def get_watch_list(self, watch_name):
        url = "https://api.tdameritrade.com/v1/accounts/279952546/watchlists"
        all_lists = rC.use_requests_return_json(url, headers=self.auth_header)
        for wl in all_lists:
            if wl['name'].lower() == watch_name.lower():
                return [x["instrument"]["symbol"].replace("$", "") for x in wl["watchlistItems"]]


def main():
    tda = TdRequests()
    wl = tda.get_watch_list("Carbon")
    stop = 1


if __name__ == '__main__':
    main()
