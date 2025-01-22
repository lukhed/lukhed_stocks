from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC
from resources.aceCommon import stringCommon as sC
from resources.aceCommon import timeCommon as tC


class Webull:
    def __init__(self, add_delay_as_float=None, keep_live_cache=True, use_basics_cache=False, basics_cache_loc=None,
                 use_proxies=False):
        """
        :param add_delay_as_float:      float()/int(), if you provide a value, there will be a delay equal to that
                                        value in seconds each time before making a call to webull server. Each
                                        function has a different delay as it depends on how many different calls are
                                        needed to webull. Check each function comments.

        :param keep_live_cache:         bool(), if True each quote or all data retrieved from webull will be
                                        cached in a working list. If you call the same symbol and same function again,
                                        or if you use another function that makes use of the same data, the live
                                        cache will be used instead of calling webull fresh. This can save a lot of
                                        time but at the cost of freshness of data.

        :param use_basics_cache:        bool(), if True basic information about tickers will be loaded and saved on
                                        the hard disk for use across instantiations. This is good to save on webull
                                        calls, as each webull call for a symbol requires a webull search to get symbol
                                        specific webull id. Basics cache will store webull id's for tickers as
                                        well as other basic info like exchange. Use the refresh parameter to update
                                        this periodically.

        :param basics_cache_loc:        str(), if basics_cache is True, the default location is the directory where
                                        the script is located, and this parameter can stay None. If you want to store
                                        somewhere other than default, pass the directory string here (full path).

        :param use_proxies:             bool()

        """

        self.use_proxies = use_proxies
        if self.use_proxies:
            self.proxy_requests = rC.ScrapingRequestsWithProxy()
        else:
            self.proxy_requests = None

        self.base_api_url = 'https://quotes-gw.webullfintech.com/api/'
        self._error_dict = {"searchedSymbol": "", "error": False, "errorMessage": ""}

        # Cache settings
        self.keep_live_cache = keep_live_cache
        self.use_basics_cache = use_basics_cache

        # Cache dicts
        self.quote_cache = {}
        self.all_data_cache = {}
        if self.use_basics_cache:
            if basics_cache_loc is None:
                self.basics_cache_loc = osC.create_file_path_string(["webullBasicsCache.json"])
            else:
                self.basics_cache_loc = osC.append_to_dir(basics_cache_loc, "webullBasicsCache.json")

            if osC.check_if_file_exists(self.basics_cache_loc, full_path=True) == 1:
                self.basics_cache = fC.load_json_from_file(self.basics_cache_loc)
            else:
                self.basics_cache = {}
        else:
            self.basics_cache = {}

        self.delay = add_delay_as_float

    def __del__(self):
        if self.use_basics_cache:
            fC.dump_json_to_file(self.basics_cache_loc, self.basics_cache)

        if self._error_dict["error"]:
            print("Last error logged is: " + self._error_dict["errorMessage"])

    def _parse_symbol(self, symbol):
        symbol = str(symbol)
        symbol = symbol.lower()
        symbol = symbol.replace(".", "-")
        return symbol

    def _parse_input_for_function_working_on_add_data(self, symbol, provided_data):
        if provided_data is None:
            return self.get_symbol_additional_data(symbol)
        else:
            return provided_data

    def _check_add_delay(self):
        if self.delay is None:
            pass
        else:
            tC.sleep(self.delay)

    def _add_to_cache(self, cache_type, symbol, data):
        """
        Call this function every time after you make a call to webull to get a quote or all data. It will check
        if the cache setting is on and add the quote to cache if it is.

        Cache type is either quote or all data

        :param cache_type:          str(), quote, all data, basics
        :param symbol:              str(), ticker symbol
        :return:                    None
        """

        symbol = symbol.lower()
        if self.keep_live_cache:
            if cache_type == 'quote':
                self.quote_cache[symbol] = data
            elif cache_type == 'all data':
                self.all_data_cache[symbol] = data
            elif cache_type == 'basics':
                self.basics_cache[symbol] = data

    def _check_cache_before_calling(self, cache_type, symbol):
        """
        Call this function every time before calling webull to see if the data is already in cache. It will check the
        cache setting is on and if it is then it will try the cache for the data.

        :param cache_type:          str(), quote, all data
        :param symbol:              str(), ticker symbol
        :return:                    dict() or None
        """

        def _try_cache():
            try:
                return temp_cache[symbol]
            except KeyError:
                return None

        symbol = self._parse_symbol(symbol)
        temp_cache = {}
        if self.keep_live_cache:
            # Try quote cache and all data cache as quote is within it
            if cache_type == 'quote':
                temp_cache = self.quote_cache
                r = _try_cache()

                if r is None:
                    temp_cache = self.all_data_cache
                    r = _try_cache()
                    if r is None:
                        return None
                    else:
                        return r['tickerRT']
                else:
                    return r

            elif cache_type == 'all data':
                temp_cache = self.all_data_cache
                return _try_cache()

            elif cache_type == 'basics':
                temp_cache = self.basics_cache
                return _try_cache()

        else:
            return None

    def _get_quote_field(self, value, quote):
        value = value.lower()
        if 'exchange' in value:
            try:
                return quote['disExchangeCode']
            except KeyError:
                self._error_dict["error"] = True
                self._error_dict["errorMessage"] = "Exchange field does not exist in quote. Error in _get_quote_field"
                return None
        elif 'tickerid' in value:
            try:
                return str(quote['tickerId'])
            except KeyError:
                self._error_dict["error"] = True
                self._error_dict["errorMessage"] = "tickerId field does not exist in quote. Error in _get_quote_field"
                return None

    def _call_webull_for_ticker_lookup(self, symbol):
        """
        This function does a search on the ticker to get ticker id and other basic info which is needed for all other
        supported calls (all data or quote).

        This class always caches basic search data for symbols (for purposes of keeping id and exchange during a
        single session). This saves on the need to do multiple searches on the same ticker, as this data freshness
        does not matter. You can opt to save the single session cache across sessions by uses "use_basics_cache".

        :param symbol:
        :return:
        """

        cache_result = self._check_cache_before_calling("basics", symbol)
        if cache_result is not None:
            return cache_result

        search_url = 'search/pc/tickers?keyword=' + symbol + '&regionId=6&pageIndex=1&pageSize=1'

        self._check_add_delay()
        search_response = rC.use_requests_return_json(self.base_api_url + search_url, add_user_agent='yes')
        try:
            ticker_find = search_response['data'][0]
        except KeyError or IndexError:
            self._error_dict["error"] = True
            self._error_dict["errorMessage"] = "Could not find ticker using webull search api=" + symbol
            self._error_dict["searchedSymbol"] = symbol
            return self._error_dict.copy()

        if ticker_find['disSymbol'].lower() == symbol.lower():
            ticker_find['error'] = False
            ticker_find['errorMessage'] = ""
            ticker_find["searchedSymbol"] = symbol
            self._add_to_cache("basics", symbol, ticker_find)
            return ticker_find
        else:
            self._error_dict["error"] = True
            self._error_dict["errorMessage"] = "Error parsing webull search result=" + symbol
            self._error_dict["searchedSymbol"] = symbol
            return self._error_dict.copy()

    def _call_webull_for_quote(self, symbol):
        # Get basic data. If delay is in use, this function will have that delay as it calls webull
        ticker_basics = self._call_webull_for_ticker_lookup(symbol)
        if ticker_basics is None:
            return self._error_dict.copy()

        # Get ticker Id
        try:
            ticker_id = str(ticker_basics['tickerId'])
        except KeyError:
            self._error_dict["error"] = True
            self._error_dict["errorMessage"] = "No ticker ID available for " + symbol
            self._error_dict["searchedSymbol"] = symbol
            return self._error_dict.copy()

        # Craft URL for quote
        q_url_1 = 'stock/tickerRealTime/getQuote?tickerId='
        q_url_2 = '&includeSecu=1&includeQuote=1&more=1'
        quote_url = (self.base_api_url + q_url_1 + ticker_id + q_url_2)

        # Call webull for quote
        self._check_add_delay()
        try:
            quote = rC.use_requests_return_json(quote_url, add_user_agent="yes")
            quote.update({"error": False, "errorMessage": None})
        except:
            self._error_dict["error"] = True
            self._error_dict["errorMessage"] = "Error in using webull quote api for " + symbol
            self._error_dict["searchedSymbol"] = symbol
            return self._error_dict.copy()

        # Check if should add to live cache and add if setting is true.
        quote["searchedSymbol"] = symbol
        self._add_to_cache("quote", symbol, quote)

        return quote

    def _call_webull_for_all_data(self, symbol):
        """
        This is under the hood for the all data function. This uses a scraping technique to get all data for the
        symbol because there is not a call-able api for all of this data.

        :param symbol:
        :return:
        """

        # First get ticker basics. If delay is in use, a delay will be incurred here as webull is called
        ticker_basics = self._call_webull_for_ticker_lookup(symbol)
        if ticker_basics["error"]:
            return ticker_basics

        # Extract the basic info needed to make a profile call
        try:
            ticker_id = str(ticker_basics['tickerId'])
            exchange_code = str(ticker_basics['disExchangeCode'])
        except:
            self._error_dict["error"] = True
            self._error_dict["errorMessage"] = "Error parsing data from webull search response for " + symbol
            self._error_dict["searchedSymbol"] = symbol
            return self._error_dict.copy()

        # Create the URL for stock profile page
        profile_url = 'https://www.webull.com/quote/' + exchange_code.lower() + '-' + symbol.lower() + '/profile'

        # Get soup of profile page
        self._check_add_delay()
        try:
            if self.use_proxies:
                soup = self.proxy_requests.basic_request_use_proxy(profile_url, add_user_agent=True, return_soup=True)
            else:
                soup = rC.get_soup(profile_url, add_user_agent=True)
        except:
            self._error_dict["error"] = True
            self._error_dict["errorMessage"] = "Can't get profile soup for " + symbol + ". (_call_webull_for_all_data)"
            self._error_dict["searchedSymbol"] = symbol
            return self._error_dict.copy()

        # Parse the soup and isolate the profile data
        try:
            profile_content = soup.find("script", {"id": 'server-side-script'})
            stock_data = profile_content.text.strip()
            stock_data = stock_data.replace("window.__initState__=", "")
            stock_data = stock_data.replace("};", "}")
            stock_dict = sC.convert_string_to_json(stock_data)
            profile_dict = stock_dict['tickerMap'][ticker_id]
            profile_dict["error"] = False
            profile_dict["errorMessage"] = ""
            profile_dict["searchedSymbol"] = symbol
        except:
            self._error_dict["error"] = True
            self._error_dict["errorMessage"] = "Can't parse profile soup for " + symbol + " (_call_webull_for_all_data)"
            self._error_dict["searchedSymbol"] = symbol
            return self._error_dict.copy()

        self._add_to_cache("all data", symbol, profile_dict)

        return profile_dict

    def get_quote(self, symbol):
        """
        Use this function if you just want the basics for a ticker and no additional market data.
        :param symbol:
        :return:
        """

        symbol = self._parse_symbol(symbol)
        cache_result = self._check_cache_before_calling("quote", symbol)
        if cache_result is not None:
            return cache_result
        else:
            return self._call_webull_for_quote(symbol)

    def get_symbol_additional_data(self, symbol):
        """
        Use this function to get all data for a ticker. Example of data that can be retrieved with this is found
        here:
        https://www.webull.com/quote/nasdaq-meta/profile


        :param symbol:
        :return:
        """

        symbol = self._parse_symbol(symbol)
        cache_result = self._check_cache_before_calling("all data", symbol)

        if cache_result is not None:
            return cache_result
        else:
            return self._call_webull_for_all_data(symbol)

    def get_grouping_data(self, symbol, provide_add_data=None):
        symbol_data = self._parse_input_for_function_working_on_add_data(symbol, provide_add_data)
        sectors = symbol_data['stockCompBriefs']['sectors']

        op_list = []
        counter = 0
        for sector in sectors:
            op_list.append(
                {"grouping": sector['name'],
                 "totalTickersInGroup": sector['advancedNum'] + sector['declinedNum'],
                 "totalAdvanced": sector['advancedNum'],
                 "totalDeclined": sector['declinedNum']
                 })
            counter = counter + 1

        return op_list

    def get_sector_data(self, symbol, provide_add_data=None):
        symbol_data = self._parse_input_for_function_working_on_add_data(symbol, provide_add_data)
        try:
            sector_name = symbol_data['stockCompBriefs']['about']['industryName']
        except KeyError:
            return 'n/a'


def testing():
    pc_dir = osC.create_root_path_starting_from_drive("C:")
    webull_cache = osC.append_to_dir(pc_dir, ["Users", "heide", "Documents", "Luke", "Programming", "grindSundayStocks",
                                              "resources", "grindSundayStocks", "webull_cache"], list=True)
    w = Webull(use_basics_cache=True, basics_cache_loc=webull_cache, use_proxies=False)
    # test_data = w.get_grouping_data("BOX")
    add_data = w.get_symbol_additional_data("META")
    stop = 1


if __name__ == '__main__':
    testing()
