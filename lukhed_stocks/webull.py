from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC
from lukhed_basic_utils import osCommon as osC
from lukhed_basic_utils import fileCommon as fC

class Webull:
    def __init__(self, api_delay=0.5, keep_live_cache=False, use_basics_cache=False, refresh_basics_cache=False):
        """
        :param api_delay:               float()/int(), if you provide a value, there will be a delay equal to that
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
        :param refresh_basics_cache:   bool(), if True the basics cache will be refreshed from webull on
                                        instantiation. This is useful to keep your basics cache up to date.
        """
        self.api_delay = api_delay
        self.base_api_url = 'https://quotes-gw.webullfintech.com/api/'
        self._error_dict = {"searchedSymbol": "", "error": False, "errorMessage": ""}

        self.quote_cache = {}
        self.all_data_cache = {}
        self.delay = api_delay

        # Cache settings
        self.keep_live_cache = keep_live_cache
        self.use_basics_cache = use_basics_cache

        if self.use_basics_cache:
            self.basics_cache_loc = osC.create_file_path_string(["lukhedCache", "webullBasicsCache.json"])
            if refresh_basics_cache:
                self.basics_cache = {}
                fC.dump_json_to_file(self.basics_cache_loc, self.basics_cache)
                
            if osC.check_if_file_exists(self.basics_cache_loc):
                self.basics_cache = fC.load_json_from_file(self.basics_cache_loc)
            else:
                self.basics_cache = {}
        else:
            self.basics_cache = {}

    def _parse_symbol(self, symbol):
        symbol = str(symbol)
        symbol = symbol.lower()
        symbol = symbol.replace(".", "-")
        return symbol

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
        search_response = rC.request_json(self.base_api_url + search_url, add_user_agent=True)
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
            quote = rC.request_json(quote_url, add_user_agent=True)
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
    
    def __del__(self):
        if self.use_basics_cache:
            fC.dump_json_to_file(self.basics_cache_loc, self.basics_cache)

        if self._error_dict["error"]:
            print("Last error logged is: " + self._error_dict["errorMessage"])

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
        
