from schwab import auth
from lukhed_basic_utils.githubCommon import KeyManager
from typing import Optional
from lukhed_basic_utils import osCommon as osC
from lukhed_basic_utils import timeCommon as tC
from lukhed_basic_utils import fileCommon as fC
from lukhed_basic_utils import listWorkCommon as lC
from lukhed_basic_utils import mathCommon as mC

class SchwabPy:
    """
    Notes for development:

    https://pypi.org/project/schwab-py/

    Note1: Whenever you write a new endpoint function, you need to make sure you check for access token update after
    a call, as the schwab library manages the refresh token. You also should add the except logic for unexpected token
    expiration, incase the token is expired (7 day access only). See the golden example in _get_quote_endpoint.

    By default, this class will try to create a valid API from a token file. The token file is valid for
    7 days. If you have not used this class for 7 days or have not re-authenticated, then it will prompt
    you to re-authenticate.

    """

    def __init__(self, use_ticker_cache=False, verbose=True, use_api_delay=True, force_new_token=False, 
                 key_management='github', schwab_api_setup=False):

        osC.check_create_dir_structure(['lukhedConfig'])
        self.key_management = key_management.lower()
        self._token_file_path = osC.create_file_path_string(['lukhedConfig', 'localTokenFile.json'])
        self.api = None                                 # type: Optional[auth.easy_client]
        self._api_key = None
        self._app_secret = None
        self._callback_url = None
        self._access_token = None

        if schwab_api_setup:
            self._schwab_api_setup()

        # utilized objects
        self.kM = None                                  # type: Optional[KeyManager]
        self._key_data = None

        # Load access data
        self._check_create_km()

        # class settings
        self.quote_cache = []
        self.keep_cache = True if use_ticker_cache else False
        self.verbose = verbose
        self.api_delay = use_api_delay
        self.force_new_token = force_new_token

        self.create_api_from_access_token()

    def _schwab_api_setup(self):
        print("This is the lukhed setup for Schwab API wrapper. If you haven't already, you first need to setoup a"
              " Schwab api developer acccount (free). To continue, you need the following from the setup:\n"
              "1. App Key\n"
              "2. Secret\n"
              "3. Callback URL\n"
              "If you don't know how to get these, you can find instructions here:\n"
              "https://schwab-py.readthedocs.io/en/latest/getting-started.html")
        
        if input("\n\nAre you ready to continue (y/n)?") == 'n':
            print("OK, come back when you have setup your developer account")
            quit()

        self._api_key = input("Paste your App key then press enter:\n").replace(" ", "")
        self._app_secret = input("Paste your Secret, then press enter:\n").replace(" ", "")
        self._callback_url = input("Paste your Callback URL here:\n").replace(" ", "")

        self.api = auth.client_from_login_flow(self._api_key, self._app_secret, self._callback_url,
                                               self._token_file_path)

        # write the new token to github
        tC.sleep(1)
        self._access_token = fC.load_json_from_file(self._token_file_path)
        key_data = self._build_key_file()

        print("\n\nThe Schwab portion is complete! Now setting up key management with lukhed library...")
        self.kM = KeyManager('schwabApi', config_file_preference=self.key_management, 
                             provide_key_data=key_data)


    def _check_create_km(self):
        if self.kM is None:
            # get the key data previously setup and make sure local token file schwab uses is up to date
            self.kM = KeyManager('schwabApi', config_file_preference=self.key_management)
            self._api_key = self.kM.key_data['account']['appKey']
            self._app_secret = self.kM.key_data['account']['secret']
            self._callback_url = self.kM.key_data['account']['callbackUrl']
            self._access_token = self.kM.key_data['token']
            fC.dump_json_to_file(self._token_file_path, self._access_token)
    
    
    def _print(self, s):
        if self.verbose:
            print(s)

    """
    **************************
    Custom Helper Functions
    **************************
    """
    def _parse_quote_cache_parameters_and_check_cache(self, ticker):
        """
        This function checks to see if cache is enabled. If it is enabled, it looks to see if a quote was already
        pulled for the given ticker. If it was already pulled, it returns that ticker. This is used by
        get_stock_quote to utilize the cache.

        :param ticker:
        :return:
        """
        if self.keep_cache:
            ticker = ticker.upper()
            cache_check = lC.check_for_value_in_list_of_dicts_given_key(self.quote_cache, "symbol", ticker)

            if cache_check is not None:
                self._print(f"Utilized cache for {ticker}")
                return cache_check
        else:
            return None

    """
    **************************
    Auth functionality
    **************************
    """
    def _unexpected_token_expired_flow(self):
        refresh_input = input("\n\nERROR: Token is expired. Do you want to refresh it? (y/n):")

        if refresh_input == 'y':
            print("Initiating refresh sequence...")
            self.create_api_from_new_authentication()
    
    def _build_key_file(self):
        full_key_data = {
            "account": {"appKey": self._api_key, "secret": self._app_secret, "callbackUrl": self._callback_url},
            "token": self._access_token
        }
        return full_key_data
    
    def _check_for_access_token_updates(self):
        currently_used_token = fC.load_json_from_file(self._token_file_path)
        if currently_used_token != self._access_token:
            print("new token created by refresh token within the api")
            self._access_token = currently_used_token
            key_data = self._build_key_file()
            self.kM.force_update_key_data(key_data)

    def create_api_from_access_token(self):

        if not self.force_new_token:
            try:
                self.api = auth.easy_client(self._api_key, self._app_secret, self._callback_url, self._token_file_path)
            except FileNotFoundError:
                print("ERROR: The token file must have been deleted. You need to re-authenticate.")
                self.create_api_from_new_authentication()
        else:
            self._print("INFO: The class was instantiated with force_new_token set to True. Starting the token flow...")
            self.create_api_from_new_authentication()

    def create_api_from_new_authentication(self):
        """
        This function creates a new access token. Schwab requires this to be done manually every week (7 days).

        :return:
        """
        self.api = auth.client_from_login_flow(self._api_key, self._app_secret, self._callback_url,
                                               self._token_file_path)

        # write the new token to github
        tC.sleep(1)
        self._access_token = fC.load_json_from_file(self._token_file_path)
        key_data = self._build_key_file()
        self.kM.force_update_key_data(key_data)

    """
    **************************
    Endpoint Wrappers and their helper functions
    **************************
    """
    # Get Quotes
    def _get_quotes_endpoint(self, ticker, retry_times, retry_attempt=False):
        """
        This function makes a call to the get_quotes endpoint and returns the data.
        https://schwab-py.readthedocs.io/en/latest/client.html#schwab.client.Client.get_quotes

        'Get quote for a symbol. This method supports all symbols, including those containing
        non-alphanumeric characters like /ES.'

        :param ticker:          str() or list(), the ticker to get the quote from. 500 tickers is max.
        :param retry_times:     int(), the amount of times we should retry the endpoint if there is a failure
        :param retry_attempt:   bool(), used by retry logic function as to not create infinite loops
        :return:                dict(), custom dict with the endpoint response and success analysis
        """

        if type(ticker) == list:
            ticker = [x.upper() for x in ticker]
            input_type_list = True
        else:
            ticker = ticker.upper()
            input_type_list = False

        # api call
        self._parse_api_delay()
        quote = self.api.get_quotes(ticker)
        self._check_for_access_token_updates()

        status_code = quote.status_code
        status_notes = None

        retry_times = 0 if retry_attempt else retry_times

        if status_code == 200:
            meta_data = self._parse_200_response_quote_endpoint(quote)
            status_notes = meta_data['statusCodeNotes']
            success = meta_data['success']

        elif retry_times > 0:
            success, quote = self._get_quote_endpoint_retry_logic(ticker, status_code, retry_times)
            status_code = quote.status_code

            if success == 200:
                meta_data = self._parse_200_response_quote_endpoint(quote)
                status_notes = meta_data['statusCodeNotes']
                success = meta_data['success']

        else:
            success = False

        return {"quote": quote, "success": success, "statusCode": status_code, "statusCodeNotes": status_notes}

    @staticmethod
    def _parse_200_response_quote_endpoint(quote):
        """
        Sometimes the quote endpoint returns 200 but there is no data for a ticker. So this function parses the
        200 responses and handles the possible responses we get from the API.

        :param quote:
        :return:
        """
        status_code = quote.status_code
        status_notes = None
        if quote.json() == {}:
            success = False
            status_notes = "no data in quote"
            status_code = 200
        else:
            success = True

        return {"success": success, "statusCode": status_code, "statusCodeNotes": status_notes}

    def _parse_quote_endpoint_data(self, ep_data, ticker):
        """
        This function puts the quote endpoint data into the format that is utilized by class.

        :param ep_data:         dict(), the data returned by the quote endpoints
        :param ticker:          str(), the ticker that was searched
        :return:
        """

        if type(ticker) == list:
            ticker = [x.upper() for x in ticker]
            input_type_list = True
        else:
            ticker = ticker.upper()
            input_type_list = False

        if ep_data['success']:
            op_json = ep_data['quote'].json()

            if input_type_list:
                op_json = [op_json[x] for x in list(op_json.keys())]
                for i, quote in enumerate(op_json):
                    try:
                        quote['invalidSymbols']
                        quote.update({"error": True})
                    except KeyError:
                        quote.update({"error": False})
                    quote.update({"errorCodeNotes": ep_data['statusCodeNotes']})
                    op_json[i]['cacheKey'] = ticker[i]
                    if self.keep_cache:
                        check_cache = lC.check_for_value_in_list_of_dicts_given_key(
                            self.quote_cache, 'symbol', quote['symbol'])
                        if check_cache is None:
                            self.quote_cache.append(quote.copy())
            else:
                dict_key = list(op_json.keys())[0]
                op_json = op_json[dict_key]
                try:
                    test = op_json['invalidSymbols']
                    op_json.update({"error": True})
                except KeyError:
                    op_json.update({"error": False})

                op_json.update({"errorCodeNotes": ep_data['statusCodeNotes']})
                op_json.update({'cacheKey': ticker})
                if self.keep_cache:
                    self.quote_cache.append(op_json.copy())

            return op_json
        else:
            return {"ticker": ticker, "error": True, "errorCode": ep_data['statusCode'],
                    "errorComments": ep_data['statusCodeNotes']}

    def _parse_api_delay(self, force_delay=False):
        if self.api_delay or force_delay:
            tC.sleep(0.75)

    def _get_quote_endpoint_retry_logic(self, ticker, status_code, retry_times):
        """
        This is the retry logic that is initiated by the get_stock_quote function. It works in conjunction with the
        _get_quotes_endpoint function.

        :param ticker:
        :param status_code:
        :param retry_times:
        :return:
        """
        i = 0
        quote = None

        while i < retry_times:
            if status_code == 429:
                self._print(f"ERROR: error {status_code} on {ticker}...Given the error, adding 1 minute delay.")
                tC.sleep(60)
            else:
                self._print(f"ERROR: error {status_code} on {ticker}...Adding a small api delay and retrying.")
                self._parse_api_delay(force_delay=True)

            ep_data = self._get_quotes_endpoint(ticker, None, retry_attempt=True)

            quote = ep_data['quote']
            if ep_data['statusCode'] == 200:
                self._print("Successful re-attempt on ticker: " + ticker)
                return True, quote
            else:
                self._print(f"Failed on re-attempt {i} for {ticker}...")

            i = i + 1

        self._print(f"ERROR: Reattempts for {ticker} failed.")
        return False, quote

    @staticmethod
    def _create_quote_error_dict(quote_data, special_note=None):
        return {"error": True, "errorCodeNotes": quote_data['errorCodeNotes'], "data": quote_data.copy(),
                "specialNote": special_note}

    """
    **************************
    Endpoint Wrappers and their helper functions
    **************************
    """
    def get_stock_quote(self, ticker_or_tickers, retry_times=0, last_price_only=False):
        """
        :param ticker_or_tickers:   str() or list(), max 500
        :return:                    dict(), ticker information
        """

        ticker = ticker_or_tickers
        if type(ticker) == list:
            ticker = [x.upper() for x in ticker]
            input_type_list = True
        else:
            ticker = ticker.upper()
            input_type_list = False

        # Check if cache is on and if info is already in cache
        if not input_type_list:
            cache_check = self._parse_quote_cache_parameters_and_check_cache(ticker)
            if cache_check is not None:
                return cache_check

        # Not in cache so use the endpoint
        ep_data = self._get_quotes_endpoint(ticker, retry_times)
        op_data = self._parse_quote_endpoint_data(ep_data, ticker)

        if ep_data['success']:
            if last_price_only:
                if input_type_list:
                    new_op_data = []
                    for data in op_data:
                        if data['error']:
                            new_op_data.append(self._create_quote_error_dict(data, 'Error in quote data'))
                        else:
                            new_op_data.append({"ticker": data['cacheKey'],
                                                "dataPoint": data['quote']['lastPrice'],
                                                "error": False})
                else:
                    if op_data['error']:
                        op_data = self._create_quote_error_dict(op_data, "Error in quote data")
                    else:
                        op_data = {"ticker": op_data['cacheKey'],
                                   "dataPoint": op_data['quote']['lastPrice'],
                                   "error": False}

        return op_data

    def get_stock_price(self, ticker, retry_times=0, provide_quote=None):
        """
        This function utilizes the get quotes endpoint, it will also use cache if the class is instantiated with
        that parameter.

        :param retry_times:
        :param provide_quote:       dict(), quote dict and this function will use the provided quote and access the
                                    last price information

        :return:                    the last price for the ticker or None if there is an error or no price.
        """

        if provide_quote is not None:
            return provide_quote['quote']['lastPrice']

        # Check if cache is on and if info is already in cache
        cache_check = self._parse_quote_cache_parameters_and_check_cache(ticker)
        if cache_check is not None:
            return cache_check['quote']['lastPrice']

        # Not in cache and quote not provided, so use the quote endpoint
        quote_data = self.get_stock_quote(ticker, retry_times)

        if quote_data['error']:
            return self._create_quote_error_dict(quote_data)
        else:
            return {"error": False, "dataPoint": quote_data['quote']['lastPrice']}

    def get_stock_52w_low(self, ticker, retry_times=0, provide_quote=None):
        if provide_quote is not None:
            return provide_quote['quote']['52WeekLow']

        # Check if cache is on and if info is already in cache
        cache_check = self._parse_quote_cache_parameters_and_check_cache(ticker)
        if cache_check is not None:
            return cache_check['quote']['52WeekLow']

        # Not in cache and quote not provided, so use the quote endpoint
        quote_data = self.get_stock_quote(ticker, retry_times)

        if quote_data['error']:
            return self._create_quote_error_dict(quote_data)
        else:
            return {"error": False, "dataPoint": quote_data['quote']['52WeekLow']}

    def get_stock_52w_high(self, ticker, retry_times=0, provide_quote=None):
        if provide_quote is not None:
            return provide_quote['quote']['52WeekHigh']

        # Check if cache is on and if info is already in cache
        cache_check = self._parse_quote_cache_parameters_and_check_cache(ticker)
        if cache_check is not None:
            return cache_check['quote']['52WeekHigh']

        # Not in cache and quote not provided, so use the quote endpoint
        quote_data = self.get_stock_quote(ticker, retry_times)

        if quote_data['error']:
            return self._create_quote_error_dict(quote_data)
        else:
            return {"error": False, "dataPoint": quote_data['quote']['52WeekHigh']}

    def get_percent_above_52w_low(self, ticker, retry_times=0, provide_quote=None):
        if provide_quote:
            quote = provide_quote
        else:
            quote = self.get_stock_quote(ticker, retry_times=retry_times)

        if quote['error']:
            return self._create_quote_error_dict(quote)
        else:
            price = self.get_stock_price(ticker, retry_times=0, provide_quote=quote)
            low = self.get_stock_52w_low(ticker, retry_times=0, provide_quote=quote)

        if low != 0:
            dp = mC.pretty_round_function(100 * ( (price - low) / low), 2)
            return {"error": False, "dataPoint": dp}
        else:
            error_note = 'Could not calculate: 52wk low is listed as 0'
            return self._create_quote_error_dict(quote, special_note=error_note)

    def get_percent_below_52w_high(self, ticker, retry_times=0, provide_quote=None):
        if provide_quote:
            quote = provide_quote
        else:
            quote = self.get_stock_quote(ticker, retry_times=retry_times)

        if quote['error']:
            return self._create_quote_error_dict(quote)
        else:
            price = self.get_stock_price(ticker, retry_times=0, provide_quote=quote)
            high = self.get_stock_52w_high(ticker, retry_times=0, provide_quote=quote)

        if high != 0:
            dp = mC.pretty_round_function(100 * ( (high - price) / high), 2)
            return {"error": False, "dataPoint": dp}
        else:
            error_note = 'Could not calculate: 52wk high is listed as 0'
            return self._create_quote_error_dict(quote, special_note=error_note)

    # Special symbols
    def get_crypto_quote(self, friendly_crypto_symbol, retry_times=0, last_price_only=False):
        ticker = f'/{friendly_crypto_symbol.upper()}'
        quote = self.get_stock_quote(ticker, retry_times=retry_times)

        if quote['error']:
            return self._create_quote_error_dict(quote)
        else:
            if last_price_only:
                dp = quote['lastPrice']
                return {"error": False, "dataPoint": dp}
            else:
                return quote

    def get_major_index_quotes(self, last_price_only=False):
        """
        A convenience function to get data on the major indices. This function will not use cache.

        :param last_price_only:     bool(), if you just want the last price listed and not the full quote.
        :return:                    list(), list of dicts with the indice data  according to parameters.
        """

        friendly = {'/ES': 'S&P',
                    '/YM': 'Dow',
                    '/NQ': 'Nasdaq',
                    '/RTY': 'Russel 2000'}
        quotes = self.get_stock_quote(['/ES', '/YM', '/NQ', '/RTY'])

        op_data = []
        for q in quotes:
            key = q['cacheKey']
            if last_price_only:
                op_data.append({"index": friendly[key], "dataPoint": q['quote']['lastPrice']})
            else:
                op_data.append({"index": friendly[key], "dataPoint": q.copy()})

        return op_data