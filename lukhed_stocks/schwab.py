from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import githubCommon as gC
from resources.aceCommon import timeCommon as tC
from resources.aceCommon import listWorkCommon as lC
from resources.aceCommon import mathCommon as mC
from typing import Optional
from schwab import auth, client
from authlib.integrations.base_client.errors import OAuthError


class SchwabPy:
    """
    Notes for development:

    https://pypi.org/project/schwab-py/

    Note1: Whenever you write a new endpoint function, you need to make sure you check for access token update after
    a call, as the api manages the refresh token. You also should add the except logic for unexpected token
    expiration, incase the token is expired (7 day access only). See the golden example in _get_quote_endpoint.

    """

    def __init__(self, use_ticker_cache=False, verbose=True, use_api_delay=True, force_new_token=False,
                 force_client_from_token_file=False):
        """
        By default, this class will try to create a valid API from a token file. The token file is valid for
        7 days. If you have not used this class for 7 days or have not re-authenticated, then it will prompt
        you to re-authenticate.

        :param use_ticker_cache:    bool(), if True, all stock quotes retrieved within a session will be kept in a
                                    session cache, and upon a new attempt to retrieve a quote, the cache will be
                                    tried first. Use this if exactness of price is not needed during retrieval of
                                    many tickers with potential repeats (e.g., after close).
        """

        # utilized objects
        self.api = None                                 # type: Optional[client]
        self.gh = gC.GitCommon(repo_name='stocks')

        # class settings
        self.quote_cache = []
        self.keep_cache = True if use_ticker_cache else False
        self.verbose = verbose
        self.api_delay = use_api_delay
        self.force_new_token = force_new_token

        # authenticate data
        self.key_github_path = ['resources', 'commonStocks', 'keys', 'schwab_key.json']
        self.key_file_path = osC.create_file_path_string(['resources', 'commonStocks', 'keys', 'schwab_key.json'])
        self._api_key = None
        self._app_secret = None
        self._callback_url = None
        self._token_file_path = None
        self._token_github_path = None
        self._access_token = None
        self._load_access_data()

        if force_client_from_token_file:
            self._testing_force_client_from_token_file()
        else:
            self.create_api_from_access_token()


    """
    **************************
    Custom Class Helper Functions
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
            cache_check = lC.check_for_key_in_list_of_dicts_given_key(self.quote_cache, ticker)

            if cache_check is not None:
                self._print(f"Utilized cache for {ticker}")
                return cache_check
        else:
            return None

    @staticmethod
    def _parse_date_input(from_date, to_date, date_format):
        """
        Options for all dates are None, str with format, or a date-time object
        :param from_date:
        :param to_date:
        :param date_format:
        :return:
        """
        if from_date is None:
            pass
        elif type(from_date) is str:
            from_date = tC.convert_date_to_date_time(from_date, is_string=True, provided_date_format=date_format)
        else:
            pass

        if to_date is None:
            pass
        elif type(to_date) is str:
            to_date = tC.convert_date_to_date_time(to_date, is_string=True, provided_date_format=date_format)
        else:
            pass

        return from_date, to_date

    def _print(self, s):
        if self.verbose:
            print(s)

    """
    **************************
    Auth functionality
    **************************
    """
    def _load_access_data(self):
        """
        This file uses a github first method. It will always check the key on github and assume it is the latest.
        It will then upload the file on github if needed to be updated, and store a local to be used by the client.
        :return:
        """

        # Get keys file from github
        self._print("INFO: Retrieving key data from github...")
        keys = self.gh.retrieve_file_content(self.key_github_path)

        # Store data in local variables
        self._api_key = keys['apiKey']
        self._app_secret = keys['appSecret']
        self._callback_url = keys['callbackUrl']
        self._token_github_path = keys['tokenLocationList']

        # Get latest access token from github
        self._print("INFO: Retrieving access token from github...")
        self._access_token = self.gh.retrieve_file_content(self._token_github_path)

        # Write latest access token to local
        self._print("INFO: Writing github data to local pc for client use...")
        self._token_file_path = osC.create_file_path_string(keys['tokenLocationList'])    # access loc stored in file
        fC.dump_json_to_file(self._token_file_path, self._access_token)
        fC.dump_json_to_file(self.key_file_path, keys)

    def _refresh_token_expired_logic(self, e):
        if 'invalid_client' in str(e) and 'refresh token invalid' in str(e):
            print("Error: Refresh token is invalid.")
        else:
            # Handle other OAuth errors
            print(f"OAuthError occurred: {str(e)}")

        answer = input("\n Do you want to get a new token by going thru the Schwab login? (y/n): ")

        if answer == 'y':
            self.create_api_from_new_authentication()
        else:
            print("OK, quitting...")
            quit()

    def _unexpected_token_expired_flow(self):
        refresh_input = input("\n\nERROR: Token is expired. Do you want to refresh it? (y/n):")

        if refresh_input == 'y':
            print("Initiating refresh sequence...")
            self.create_api_from_new_authentication()
    def _check_for_access_token_updates(self):
        currently_used_token = fC.load_json_from_file(self._token_file_path)
        if currently_used_token != self._access_token:
            print("new token created by refresh token within the api")
            self._access_token = currently_used_token
            self.gh.create_update_file(self._token_github_path, self._access_token)

    def _testing_force_client_from_token_file(self):
        self.api = auth.client_from_token_file(self._token_file_path, self._api_key, self._app_secret)


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
        self.gh.create_update_file(self._token_github_path, self._access_token)

    """
    **************************
    SchwabPy Endpoints and their helper functions
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

        try:
            quote = self.api.get_quotes(ticker)
        except OAuthError as e:
            self._refresh_token_expired_logic(e)
            print("The token was refreshed, restart your script")
            quit()

        self._check_for_access_token_updates()

        status_code = quote.status_code
        status_notes = None

        retry_times = 0 if retry_attempt else retry_times

        if status_code == 200:
            meta_data = self._parse_200_endpoint_response(quote)
            status_notes = meta_data['statusCodeNotes']
            success = meta_data['success']

        elif retry_times > 0:
            success, quote = self._get_quote_endpoint_retry_logic(ticker, status_code, retry_times)
            status_code = quote.status_code

            if success == 200:
                meta_data = self._parse_200_endpoint_response(quote)
                status_notes = meta_data['statusCodeNotes']
                success = meta_data['success']

        else:
            success = False

        return {"quote": quote, "success": success, "statusCode": status_code, "statusCodeNotes": status_notes}

    def _get_price_history_every_blank_endpoint(self, ticker, period, from_date, to_date, extended_hours,
                                                convert_to_dts):
        ticker = ticker.upper()
        self._parse_api_delay()

        try:
            if period == 'day':
                fnc = self.api.get_price_history_every_day
            elif period == 'week':
                fnc = self.api.get_price_history_every_week
            elif period == '30 minutes':
                fnc = self.api.get_price_history_every_thirty_minutes
            elif period == '10 minutes':
                fnc = self.api.get_price_history_every_ten_minutes
            elif period == '5 minutes':
                fnc = self.api.get_price_history_every_five_minutes
            elif period == '1 minute':
                fnc = self.api.get_price_history_every_minute
            else:
                fnc = None
        except OAuthError as e:
            self._refresh_token_expired_logic(e)
            print("The token was refreshed, restart your script")
            quit()

        h = fnc(ticker, start_datetime=from_date, end_datetime=to_date, need_extended_hours_data=extended_hours).json()
        self._check_for_access_token_updates()

        if convert_to_dts:
            h = self._convert_history_to_date_times(h)

        return h

    def _get_instruments_endpoint(self, ticker, retry_times, retry_attempt=False, search_type="FUNDAMENTAL"):
        """
        Get instrument details by using different search methods.
        Also used to get fundamental instrument data by use of the FUNDAMENTAL projection

        https://schwab-py.readthedocs.io/en/latest/client.html#schwab.client.Client.get_instrume

        :param ticker:          str() or list(), the ticker to get the quote from. 500 tickers is max.
        :param retry_times:     int(), the amount of times we should retry the endpoint if there is a failure
        :param retry_attempt:   bool(), used by retry logic function as to not create infinite loops
        :param search_type:     type 'projection' or "FUNDAMENTAL" to return ticker fundamentals
        :return:                dict(), custom dict with the endpoint response and success analysis
        """

        if type(ticker) == list:
            ticker = [x.upper() for x in ticker]
        else:
            ticker = ticker.upper()

        if search_type == "FUNDAMENTAL":
            search_type = client.Client.Instrument.Projection.FUNDAMENTAL

        # api call
        self._parse_api_delay()

        try:
            r = self.api.get_instruments(ticker, search_type)
        except OAuthError as e:
            self._refresh_token_expired_logic(e)
            print("The token was refreshed, restart your script")
            quit()

        self._check_for_access_token_updates()

        status_code = r.status_code
        status_notes = None

        retry_times = 0 if retry_attempt else retry_times

        if status_code == 200:
            meta_data = self._parse_200_endpoint_response(r)
            status_notes = meta_data['statusCodeNotes']
            success = meta_data['success']

        else:
            success = False

        return {"response": r, "success": success, "statusCode": status_code, "statusCodeNotes": status_notes}

    @staticmethod
    def _convert_history_to_date_times(history_from_endpoint):
        try:
            candles = history_from_endpoint["candles"]
        except:
            candles = []

        for candle in candles:
            candle["datetime"] = tC.epoch_conversion(int(candle["datetime"]), precision="milliseconds",
                                                     output_format="%Y%m%d%H%M%S")

        return history_from_endpoint

    @staticmethod
    def _parse_200_endpoint_response(quote):
        """
        Sometimes the endpoints return 200 but there is no data. So this function parses the
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
                        test = quote['invalidSymbols']
                        quote.update({"error": True})
                    except KeyError:
                        quote.update({"error": False})
                    quote.update({"errorCodeNotes": ep_data['statusCodeNotes']})
                    op_json[i]['cacheKey'] = ticker[i]
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

    @staticmethod
    def _parse_fundamentals_endpoint_response(ep_data, ticker):
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
            response_json = ep_data['response'].json()
            dict_key = list(response_json.keys())[0]
            fundamental_json = response_json[dict_key]

            op_data = []
            for i, data in enumerate(fundamental_json):
                description = data['description']
                exchange = data['exchange']
                asset_type = data['assetType']
                cusip = data['cusip']
                ticker = ticker if not input_type_list else ticker[i]
                op_json = data['fundamental'].copy()
                op_json.update(
                    {'description': description,
                     "exchange": exchange,
                     "asset_type": asset_type,
                     "cusip": cusip,
                     "ticker": ticker}
                )
                op_data.append(op_json.copy())

            if len(op_data) == 1:
                return op_data[0]
            else:
                return op_data
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
    Core Class Functionality
    **************************
    """
    def get_stock_quote(self, ticker_or_tickers, retry_times=0, last_price_only=False):
        """
        :param last_price_only:
        :param retry_times:
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

        :param ticker:
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


    def get_price_history(self, ticker, period_type, from_date=None, to_date=None,
                          date_format_provided="%Y-%m-%d", extended_hours=None, convert_date_times=True):
        """

        :param ticker:
        :param period_type:             str(), 'week', 'day', '30 minutes', '15 minutes', '10 minutes', '5 minutes',
                                        '1 minute'
        :param from_date:
        :param to_date:
        :param date_format_provided:
        :param extended_hours:
        :param convert_date_times:
        :return:
        """

        from_date, to_date = self._parse_date_input(from_date, to_date, date_format_provided)

        fnc = self._get_price_history_every_blank_endpoint
        history = fnc(ticker, period_type, from_date, to_date, extended_hours, convert_date_times)

        return history

    def get_stock_fundamentals(self, ticker, retry_times=0):
        ep_data = self._get_instruments_endpoint(ticker, retry_times, search_type="FUNDAMENTAL")
        op_data = self._parse_fundamentals_endpoint_response(ep_data, ticker)
        return op_data


    """
    **************************
    Convenience Functions
    **************************
    """
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

    def check_token_expiration_info(self):
        created_at = self._access_token['creation_timestamp']
        expires_at = self._access_token['token']['expires_at']

        created_at_stamp = tC.convert_unix(created_at)
        expires_at_stamp = tC.convert_unix(expires_at)
        now = tC.create_time_stamp_new()

        age_data = tC.subtract_time_stamps_precise(created_at_stamp, now)
        refresh_data = tC.subtract_time_stamps_precise(now, expires_at_stamp)

        print("\n***************************************************")
        print(f'The token was created at: {created_at_stamp}')
        print(f'The token is {mC.pretty_round_function(((age_data["seconds"]/60)/60)/24, 2)} days old')
        print(f'The token needs refresh in {refresh_data["minutes"]} minutes')
        print("***************************************************\n")




def main():
    cs = SchwabPy(use_ticker_cache=True, use_api_delay=True)
    test = cs.get_stock_fundamentals('gld')
    cs.check_token_expiration_info()
    aem_history = cs.get_price_history('AEM', 'week')
    random_quotes = cs.get_stock_quote('poopy', last_price_only=True)
    # i = cs.get_major_index_quotes(last_price_only=True)
    crypto = cs.get_crypto_quote('eth')
    q = cs.get_stock_quote("AEM")
    p = cs.get_stock_price("gld")
    h = cs.get_stock_52w_high("ego")
    l = cs.get_stock_52w_low("dtm")
    hPer = cs.get_percent_below_52w_high("insw")
    lPer = cs.get_percent_above_52w_low("biti")

    stop = 1

if __name__ == '__main__':
    main()
