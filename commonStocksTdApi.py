import authlib.integrations.base_client.errors

import commonStocksIndicators
from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import timeCommon as tC
from resources.aceCommon import mathCommon as mC
from resources.aceCommon import stringCommon as strC
from resources.aceCommon import listWorkCommon as lC
from resources.aceCommon import githubCommon
import commonSelenium as sC
import tda


class Td:
    """
    Custom wrapper for tda package. This class creates a tda api that functions of the class work with.
    https://tda-api.readthedocs.io/en/stable/

    Note 1: The class requires access to github where a shared access token is kept and managed with every
            instantiation of this class. This allows the class to be used across multiple pc's without worry of token
            issues.

            https://github.com/grindSunday?tab=repositories
                -> stocks (private)
                    -> td_token_path.json

    Note 2: The token on github can expire if this class is not used for months on end. In that case, you will get
            an "invalid_grant" error when trying to use functions of this class. In this case, a new token
            file will be needed. Instantiate the class with regen_token=True. This will start the setup process
            which requires a GUI/Browser and logging into TDA.

    Note 3: The class has an optional api_delay boolean. Use this to keep under the API limit:
            All non-order based requests by personal use non-commercial applications are throttled to 120
            per minute. Exceeding this throttle limit will provide a response with a 429 error code to inform you that
            the throttle limit has been exceeded.
    """

    def __init__(self, add_api_delay=False, keep_cache=False, regen_token=False):
        """
        :param add_api_delay: bool(), should be used when you will make a lot of calls, and you don't want to get
                              throttled. Will slow down each call by 0.55 seconds:
                              'Yes. All non-order based requests by personal use non-commercial applications are
                              throttled to 120 per minute. Exceeding this throttle limit will provide a response with a
                              429 error code to inform you that the throttle limit has been exceeded.'
                              https://developer.tdameritrade.com/content/authentication-faq#:~:text=Are%20requests%20to
                              %20the%20Post,throttle%20limit%20has%20been%20exceeded.

        :param keep_cache:    bool(), if True, all stock quotes retrieved within a session will be kept in a session
                              cache, and upon a new attempt to retrieve a quote, the cache will be tried first.
                              Use this if exactness of price is not needed during retrieval of many tickers with
                              potential repeats.

                              Note: Only non-error quotes are kept in cache.

        :param regen_token:   In the event the token expires and needs to be regenerated, set this to True
                              when instantiating, and the class will go through the setup (need a browser).
        """
        self._key_dir = osC.create_file_path_string(['resources', 'commonStocks', 'keys'])

        if regen_token:
            con = input("Are you sure you want to regen the token? This should only be done if you are having "
                        "errors with permission when using the class. (y/n)")
            if con == 'y':
                self.generate_new_token_file()
            else:
                print("ok, change the regen_token parameter and try again")
                quit()

        self.api_delay = add_api_delay
        self.api = None                     # access to td through this object
        self.account_id = None
        self.account_info = None
        self._get_account_id()
        self._create_api()
        self.keep_cache = keep_cache
        self.session_cache = []

    def _create_api(self):
        """
        Creates tda api and assigns it the class value of self.api.

        The tda package handles token refresh, but the token has expiration after 90 days. So if you do not use
        the package for 90 days, you will have to recreate it. The error will be:
        "OAuthError: invalid_grant: invalid_grant". Set regen to true and retry class

        If that does not work, delete your td app and create a new one by following the instructions here. But note
        the url being used is: https://localhost:8080/
        https://tda-api.readthedocs.io/en/stable/getting-started.html

        :return: None
        """


        try:
            gh_token_content = githubCommon.retrieve_json_content_from_file("grindSunday", "stocks",
                                                                            "td_token_path.json")
            fC.dump_json_to_file(self._get_token_path(), gh_token_content)
        except:
            gh_token_content = {}
            print("ERROR: Cannot contact the github repository to get the latest token")
            quit()


        # https://tda-api.readthedocs.io/en/stable/auth.html#oauth-refresher
        self.api = tda.auth.easy_client(
            self._get_api_key(),
            self._get_redirect_url(),
            self._get_token_path(),
            sC.create_driver_no_url)

        """
        The tda api may have refreshed the token automatically, and place it into the token path we specified, 
        so we need to check. If it did, then we upload the the newly created token to github
        """
        final_token_content = fC.load_json_from_file(self._get_token_path())
        if final_token_content != gh_token_content:
            githubCommon.update_file_in_repository("grindSunday", "stocks", "td_token_path.json", final_token_content)


    def _get_account_id(self):
        account_id_file = osC.create_file_path_string(['resources', 'commonStocks', 'account', 'account_id.txt'])
        self.account_id = fC.read_single_line_from_file(account_id_file)

    def _get_api_key(self):
        key_file = osC.append_to_dir(self._key_dir, 'td_consumer_key.txt')
        api_key = fC.read_single_line_from_file(key_file)
        return api_key

    def _get_redirect_url(self):
        # This URL path must match exactly what is put in to the td app setup. Currently using: https://localhost:8080/
        url_file = osC.append_to_dir(self._key_dir, 'td_callback_url.txt')
        redirect_url = fC.read_single_line_from_file(url_file)
        return redirect_url

    def _get_token_path(self):
        token_path = osC.append_to_dir(self._key_dir, 'td_token_path.json')
        return token_path

    def _parse_api_delay(self):
        if self.api_delay:
            tC.sleep(0.75)

    def _parse_date_input(self, from_date, to_date, date_format):
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

    def _try_quote_from_cache(self, ticker):
        ticker = ticker.upper()
        return lC.check_for_key_in_list_of_dicts_given_key(self.session_cache, ticker)

    def generate_new_token_file(self):
        """
        This function should only be used when the token file expires (this class has not been used in a long time).

        :return: None, creates a new token file
        """
        # first delete the token file
        osC.delete_file(self._get_token_path())

        web_driver = sC.create_driver_no_url()
        tda.auth.client_from_login_flow(
            web_driver,
            self._get_api_key(),
            self._get_redirect_url(),
            self._get_token_path()
        )

        githubCommon.update_file_in_repository("grindSunday", "stocks", "td_token_path.json",
                                               fC.load_json_from_file(self._get_token_path()))

    def get_stock_quote(self, ticker, retry_on_fail=False):
        """
        Use this function to get quotes for single instruments, and containing all alphanumeric characters
        (i.e., a stock, not an index). Use "get_non_stock_quote" to get information about an index.

        https://tda-api.readthedocs.io/en/stable/client.html#current-quotes
        https://developer.tdameritrade.com/quotes/apis/get/marketdata/%7Bsymbol%7D/quotes

        :return: dict(), ticker information
        """
        ticker = ticker.upper()

        if self.keep_cache:
            cq = self._try_quote_from_cache(ticker)
            if cq is not None:
                return cq

        self._parse_api_delay()
        quote = self.api.get_quote(ticker)
        status_code = quote.status_code
        success = False
        if status_code == 200:
            if quote.json() == {}:
                success = False
                status_code = "200 but no data in quote"
            else:
                success = True
        else:
            if retry_on_fail:
                i = 0
                while i < 4:
                    if status_code == 429:
                        print("Error " + str(
                            status_code) + " on ticker: " + ticker + "... Adding delays and trying again")
                        print("Cooling off for a minute...")
                        tC.sleep(60)
                    else:
                        self._parse_api_delay()

                    quote = self.api.get_quote(ticker)
                    status_code = quote.status_code
                    if status_code == 200:
                        print("Successful re-attempt on ticker: " + ticker)
                        success = True
                        break
                    else:
                        print("Failed on re-attempt on ticker: " + ticker)

                    i = i + 1

        if success:
            op_json = quote.json()
            op_json.update({"error": False})
            if self.keep_cache:
                self.session_cache.append(op_json.copy())
            return op_json
        else:
            return {"ticker": ticker, "error": True, "errorCode": status_code}

    def get_non_stock_quote(self, ticker, retry_on_fail=False):
        """
        The get_quote method is not recommended for instruments with symbols symbols containing
        non-alphanumeric characters, for example as futures like /ES.
        Use this function to get quotes for these symbols.

        https://tda-api.readthedocs.io/en/stable/client.html#tda.client.Client.get_quotes
        https://developer.tdameritrade.com/quotes/apis/get/marketdata/quotes

        :param ticker:
        :param retry_on_fail
        :return: dict(), symbol information
        """

        ticker = ticker.upper()

        if self.keep_cache:
            cq = self._try_quote_from_cache(ticker)
            if cq is not None:
                return cq

        self._parse_api_delay()
        quote = self.api.get_quotes(ticker)
        status_code = quote.status_code
        success = False
        if status_code == 200:
            if quote.json() == {}:
                success = False
                status_code = "200 but no data in quote"
            else:
                success = True
        else:
            if retry_on_fail:
                i = 0
                while i < 4:
                    if status_code == 429:
                        print("Error " + str(
                            status_code) + " on ticker: " + ticker + "... Adding delays and trying again")
                        print("Cooling off for a minute...")
                        tC.sleep(60)
                    else:
                        self._parse_api_delay()

                    quote = self.api.get_quotes(ticker)
                    status_code = quote.status_code
                    if status_code == 200:
                        print("Successful re-attempt on ticker: " + ticker)
                        success = True
                        break
                    else:
                        print("Failed on re-attempt on ticker: " + ticker)

                    i = i + 1

        if success:
            op_json = quote.json()
            op_json.update({"error": False})
            if self.keep_cache:
                self.session_cache.append(op_json.copy())
            return op_json
        else:
            return {"ticker": ticker, "error": True, "errorCode": status_code}

    def get_quote_list(self, symbol_list):
        """
        Use this function to get a list of tickers. This function supports both ticker type and future type symbols.

        https://tda-api.readthedocs.io/en/stable/client.html#tda.client.Client.get_quotes
        https://developer.tdameritrade.com/quotes/apis/get/marketdata/quotes

        :return: dict(), tickers information
        """

        if self.api_delay:
            tC.sleep(0.75)

        return self.api.get_quotes(symbol_list)

    def get_price(self, ticker, index=False, provided_quote=None):
        """
        If the symbol is a future or index that has non alphanumeric characters, then use index=True.

        :param ticker: str(), ticker or symbol
        :param index: bool(), set to True if ticker provided has non alphanumeric characters.
        :param provided_quote: dict(), TDA quote object. You can pass a quote object instead of calling the API.
                               useful if you already have a recent quote pulled.
        :return: float(), last price
        """

        ticker = ticker.upper()

        if provided_quote is None:
            if index:
                return self.get_non_stock_quote(ticker)[ticker]['lastPrice']
            else:
                return self.get_stock_quote(ticker)[ticker]['lastPrice']
        else:
            return provided_quote[ticker]['lastPrice']

    def get_52w_low(self, ticker, provided_quote=None):
        if provided_quote is None:
            quote = self.get_stock_quote(ticker)
            return quote[ticker]["52WkLow"]
        else:
            return provided_quote[ticker]["52WkLow"]

    def get_52w_high(self, ticker, provided_quote=None):
        if provided_quote is None:
            quote = self.get_stock_quote(ticker)
            return quote[ticker]["52WkHigh"]
        else:
            return provided_quote[ticker]["52WkHigh"]

    def get_percent_above_52w_low(self, ticker, provide_quote=None):
        if provide_quote is None:
            quote = self.get_stock_quote(ticker)
        else:
            quote = provide_quote

        price = self.get_price(ticker, provided_quote=quote)
        low = self.get_52w_low(ticker, provided_quote=quote)
        if low != 0:
            return mC.pretty_round_function((price - low)/low, 4)
        else:
            return "error"

    def get_percent_below_52w_high(self, ticker, provide_quote=None):
        if provide_quote is None:
            quote = self.get_stock_quote(ticker)
        else:
            quote = provide_quote
        price = self.get_price(ticker, provided_quote=quote)
        high = self.get_52w_high(ticker, provided_quote=quote)
        if high != 0:
            return mC.pretty_round_function((high - price) / high, 4)
        else:
            return "error"

    def get_price_history(self, ticker, period_type, from_date=None, to_date=None,
                          date_format_provided="%Y-%m-%d", extended_hours=None, convert_date_times=True):

        history = []
        from_date, to_date = self._parse_date_input(from_date, to_date, date_format_provided)
        ticker = ticker.upper()
        if period_type == "day":
            self._parse_api_delay()
            history = self.api.get_price_history_every_day(ticker, start_datetime=from_date, end_datetime=to_date, need_extended_hours_data=extended_hours).json()
        elif period_type == "minute":
            self._parse_api_delay()
            history = self.api.get_price_history_every_minute(ticker, start_datetime=from_date, end_datetime=to_date, need_extended_hours_data=extended_hours).json()

        try:
            candles = history["candles"]
        except:
            candles = []

        if convert_date_times:
            for candle in candles:
                candle["datetime"] = tC.epoch_conversion(int(candle["datetime"]), precision="milliseconds",
                                                         output_format="%Y%m%d%H%M%S")

        return history

    def watch_list_get(self, list_name, full_details=False):
        """
        https://tda-api.readthedocs.io/en/stable/client.html#tda.client.Client.get_watchlists_for_single_account
        https://developer.tdameritrade.com/watchlist/apis/get/accounts/%7BaccountId%7D/watchlists-0

        :param list_name: str(), name of the list to retrieve in TDA
        :param full_details: bool(), By default, just a ticker list is returned. If TRUE, all data about the list
                             will come back.
        :return: list() or dict() of watch list items depending on input.
        """

        self._parse_api_delay()

        all_watch_lists = self.api.get_watchlists_for_single_account(self.account_id).json()

        wl = None
        for watch in all_watch_lists:
            if watch['name'].lower() == list_name.lower():
                if full_details:
                    return watch
                wl = watch["watchlistItems"]

        if wl is None:
            return "No matching list"
        else:
            return [x["instrument"]["symbol"] for x in wl]

    def _watch_list_get_id(self, list_name):
        self._parse_api_delay()
        wl = self.watch_list_get(list_name, full_details=True)
        return wl["watchlistId"]

    def watch_list_add_ticker(self, list_name, ticker_to_add):
        """
        Provide the list name and the ticker. The ticker will be added to the list with the current day and latest
        price available from tda.

        :param list_name:       str(), watch list name
        :param ticker_to_add:   str(), ticker to add to the list
        :return:
        """

        self._parse_api_delay()

        temp_addition = {
            "averagePrice": self.get_price(ticker_to_add),
            "purchasedDate": tC.get_date_today(return_string=True, str_format="%Y-%m-%d"),
            'instrument': {'symbol': ticker_to_add, 'assetType': 'EQUITY'}
        }

        wl = self.watch_list_get(list_name, full_details=True)

        new_list = wl["watchlistItems"].copy()
        new_list.append(temp_addition)

        self.api.update_watchlist(
            self.account_id, wl["watchlistId"],
            {'name': list_name, 'watchlistItems': new_list}
        )

    def watch_list_delete(self, list_name):
        self._parse_api_delay()
        self.api.delete_watchlist(self.account_id, self._watch_list_get_id(list_name))

    def watch_list_create(self, list_name, provided_list):
        """
        To create a watch list, you need at least one ticker.

        :param list_name:           str(), name of the list
        :param provided_list:       list(), list of strings or list of tda dicts().

                                    If a simple list of tickers is provided, this function will add basic info to the
                                    watch_list:
                                        - Date added
                                        - Price added

                                    If a list of tda dicts() is provided, this function will just pass the provided
                                    list without doing any checks.

        :return:                    bool(), True if no error, False if error
        """

        final_list = list()
        wl_spec = {
            "name": list_name,
            "watchlistItems": final_list
        }

        if type(provided_list) is str:
            return False
        else:
            if type(provided_list[0]) is dict:
                final_list = provided_list
            else:
                for ticker in provided_list:
                    ave_price = self.get_price(ticker)
                    temp_dict = {
                        "quantity": 1,
                        "averagePrice": ave_price,
                        "purchasedDate": tC.get_date_today(return_string=True, str_format="%Y-%m-%d"),
                        "instrument": {"symbol": ticker, "assetType": "EQUITY"}
                    }
                    final_list.append(temp_dict.copy())



        self.api.create_watchlist(self.account_id, wl_spec)


    def get_account_info(self):
        """
        https://tda-api.readthedocs.io/en/stable/client.html#tda.client.Client.get_account
        https://developer.tdameritrade.com/account-access/apis/get/accounts/%7BaccountId%7D-0

        :return: dict(), with account info
        """

        if self.api_delay:
            tC.sleep(0.75)
        return self.api.get_account(self.account_id, fields=[self.api.Account.Fields.POSITIONS, self.api.Account.Fields.ORDERS]).json()

    def get_fundamentals(self, ticker):
        """
        https://tda-api.readthedocs.io/en/stable/client.html#tda.client.Client.search_instruments
        https://developer.tdameritrade.com/instruments/apis/get/instruments

        :param ticker: str(), ticker
        :return: dict(), with fundamentals
        """

        if self.api_delay:
            tC.sleep(0.6)

        f = self.api.search_instruments(ticker, tda.client.Client.Instrument.Projection.FUNDAMENTAL).json()

        return f

    def get_order_history(self, from_date, to_date, provided_format='%Y-%m-%d', order_type=None, buy_sell_all="all",
                          ticker_filter=None, exact_times=False):
        """
        https://tda-api.readthedocs.io/en/stable/client.html#tda.client.Client.get_orders_by_path
        https://developer.tdameritrade.com/account-access/apis/get/accounts/%7BaccountId%7D/orders-0

        Note: Order history timestamps are UTC, 4 hours ahead of eastern time at writing. So we add 4 hours to
        provided automatically.

        :param from_date:           str(), datetime, or None. inclusive, Date must be within 60 days from today’s date.
        :param to_date:             str(), datetime, or None. Inclusive
        :param provided_format:     str(), format of dates provided
        :param order_type:          None or str(), by default returns all orders. Str options:
                                    "FILLED", "WORKING", "EXPIRED", etc. Full list here:
                                    https://tda-api.readthedocs.io/en/stable/client.html#tda.client.Client.Order
        :param buy_sell_all:        str(), all by default, returns all orders, "sell" returns only sells, "buy"
        :param ticker_filter:       str(), provide ticker to filter orders only for ticker
        :return:                    list(), list of orders
        """

        from_date, to_date = self._parse_date_input(from_date, to_date, provided_format)
        from_date = tC.add_hours_to_date_time(from_date, 4)
        to_date = tC.add_hours_to_date_time(to_date, 4)

        self._parse_api_delay()

        orders_and_legs = {}    # Provided depending on filters

        if order_type is None:
            status = None
        elif order_type.lower() == "filled":
            status = self.api.Order.Status.FILLED
        else:
            print("Unsupported order type. Need to implement that order type, returning all")
            status = None

        order_history = self.api.get_orders_by_path(self.account_id, from_entered_datetime=from_date,
                                                    to_entered_datetime=to_date, status=status).json()

        if ticker_filter is None:
            pass
        else:
            order_history, orders_and_legs = order_history_filter_by_ticker(order_history, ticker_filter)

        # Second filter by buy sell if applicable
        if buy_sell_all == "all":
            pass
        else:
            order_history, orders_and_legs = order_history_filter_by_buy_sell(order_history, buy_sell_all)

        return {
            "orderHistory": order_history,
            "applicableLegs": orders_and_legs
        }

    def get_pl_for_ticker_in_time_frame(self, from_date, to_date, ticker, provided_format='%Y-%m-%d'):
        buys = self.get_order_history(from_date, to_date, provided_format=provided_format, buy_sell_all="buy",
                                      ticker_filter=ticker, order_type="FILLED")
        tC.sleep(0.6)
        sells = self.get_order_history(from_date, to_date, provided_format=provided_format, buy_sell_all="sell",
                                       ticker_filter=ticker, order_type="FILLED")
        stop = 1


    def get_pl_dict_for_open_positions(self, ticker_filter=None):
        account_info = self.api.get_account(self.account_id, fields=self.api.Account.Fields.POSITIONS).json()
        positions = [x for x in account_info["securitiesAccount"]["positions"] if x["instrument"]["assetType"] == "EQUITY"]

        pl_dict = {}
        total_profit = 0
        for p in positions:
            tC.sleep(0.6)
            ticker = p["instrument"]["symbol"]
            current_price = self.get_price(ticker)
            average_price = p["averagePrice"]
            quantity = p["longQuantity"]

            amount_paid = quantity * average_price
            current_value = quantity * current_price

            # Format numbers how you want
            profit = mC.pretty_round_function(current_value - amount_paid, 2)
            profit_percent = mC.pretty_round_function(profit/amount_paid * 100, 2)
            day_profit = mC.pretty_round_function(p["currentDayProfitLoss"], 2)
            day_profit_percent = mC.pretty_round_function(p["currentDayProfitLossPercentage"], 2)
            total_profit = profit + total_profit

            pl_dict.update({ticker: {}})
            pl_dict[ticker].update(
                {
                    "dayProfit%": day_profit_percent,
                    "dayProfit": day_profit,
                    "totalProfit%": profit_percent,
                    "totalProfit": profit
                }
            )

        pl_dict.update({"openPositionProfit": total_profit})

        return pl_dict

    def get_bitcoin_future_price(self):
        """
        This function utilizes the underlying TD api to get the bitcoin future price.

        :return: float(), last price
        """

        return self.get_non_stock_quote("/BTC")["/BTC"]["lastPriceInDouble"]

    def summary_fundamentals(self, ticker):
        """
        Returns the dictionary for the fundamental api

        :param ticker:
        :return:
        """

        f = self.get_fundamentals(ticker)

        if f == {}:
            return "n/a"
        else:
            try:
                return self.get_fundamentals(ticker)[ticker.upper()]["fundamental"]
            except:
                print("error: on " + ticker)
                return "n/a"

    def get_volume_averages(self, ticker, period="all"):
        """

        :param ticker: str(), ticker
        :param period: str(), "all", "1d", "10d", "3m"
        :return: dict(), or float depending on period selection
        """

        f = self.summary_fundamentals(ticker)

        if f == "n/a":
            f = {
                "vol1DayAvg": None,
                "vol10DayAvg": None,
                "vol3MonthAvg": None
            }

        if period.lower() == "all":
            return {
                "oneDayAverage": f["vol1DayAvg"],
                "tenDayAverage": f["vol10DayAvg"],
                "threeMonthAverage": f["vol3MonthAvg"]
            }
        elif period == "1d":
            return f["vol1DayAvg"]
        elif period == "10d":
            return f["vol10DayAvg"]
        elif period == "3m":
            return f["vol3MonthAvg"]

    def check_mark_minervini_trend_template(self, ticker, return_full_details=False,
                                            include_criteria_descriptions=False, provide_quote=None):
        """
        Checks if the ticker meets Mark's Trend template criteria 1-7 (p. 79 Trade Like a Stock Market Wizard)

        Note: 8 cannot be checked here because it is a relative factor. This function will provide the raw
        relative strength number back if return_full_details is True so that the criteria can be calculated
        outside of this function.

        1. The current stock price is above both the 150-day (30-week) and the 200-day (40-week) moving average
           price lines.
        2. The 150-day moving average is above the 200-day moving average.
        3. The 200-day moving average line is trending up for at least 1 month (preferably 4–5 months minimum in
           most cases).
        4. The 50-day (10-week) moving average is above both the 150-day and 200-day moving averages.
        5. The current stock price is trading above the 50-day moving average.
        6. The current stock price is at least 30 percent above its 52-week low. (Many of the best selections will
           be 100 percent, 300 percent, or greater above their 52-week low before they emerge from a solid
           consolidation period and mount a large scale advance.)
        7. The current stock price is within at least 25 percent of its 52-week high
           (the closer to a new high the better).
        8. The relative strength ranking (as reported in Investor’s Business Daily) is no less than 70, and
           preferably in the 80s or 90s, which will generally be the case with the better selections. In this function,
           the raw number used to rank is calculated. The ranking cannot be calculated without reference to all
           other stocks.

        :param ticker:                          str(), ticker symbol
        :param return_full_details:             bool(), if True, return full details
        :param provide_quote:                   provide a quote saves an api call.
        :param include_criteria_descriptions:   bool(), if True, each criteria in the full details grade will have
                                                the strings describing the pass. Else will just have None in there.
        :return:                                bool(), full details or dict() or error response.
        """

        def _criteria_one(price, ma_indicators):
            ma_test_one = ma_indicators["sma150Last"]
            ma_test_two = ma_indicators["sma200Last"]
            if ma_test_one is None or ma_test_two is None:
                # the case where there isn't enough data to calculate these, then this criteria does not apply
                return True

            if price > ma_indicators["sma150Last"] and price > ma_indicators["sma200Last"]:
                return True
            else:
                return False

        def _criteria_two(ma_indicators):
            ma_test_one = ma_indicators["sma150Last"]
            ma_test_two = ma_indicators["sma200Last"]
            if ma_test_one is None or ma_test_two is None:
                # the case where there isn't enough data to calculate these, then this criteria does not apply
                return True

            if ma_indicators["sma150Last"] > ma_indicators["sma200Last"]:
                return True
            else:
                return False

        def _criteria_three(ma_indicators):
            ma_test_one = ma_indicators["sma150Last"]
            ma_test_two = ma_indicators["sma200Last"]
            if ma_test_one is None or ma_test_two is None:
                # the case where there isn't enough data to calculate these, then this criteria does not apply
                return True, "n/a"

            ma_200_y = mas["sma150Points"][-31:]
            if len(ma_200_y) < 31:
                return True, "n/a"
            ma_200_x = [i for i in range(len(ma_200_y))]
            trend_strength = mC.trend_detector(ma_200_x, ma_200_y)
            if trend_strength > 0:
                return True, trend_strength
            else:
                return False, trend_strength

        def _criteria_four(ma_indicators):
            ma_test_one = ma_indicators["sma150Last"]
            ma_test_two = ma_indicators["sma200Last"]
            ma_test_three = ma_indicators["sma50Last"]
            if ma_test_one is None or ma_test_two is None or ma_test_three is None:
                # the case where there isn't enough data to calculate these, then this criteria does not apply
                return True

            if (ma_indicators["sma50Last"] > ma_indicators["sma150Last"] and
                    ma_indicators["sma50Last"] > ma_indicators["sma200Last"]):
                return True
            else:
                return False

        def _criteria_five(price, ma_indicators):
            ma_test_one = ma_indicators["sma50Last"]
            if ma_test_one is None:
                # the case where there isn't enough data to calculate these, then this criteria does not apply
                return True

            if price > ma_indicators["sma50Last"]:
                return True
            else:
                return False

        def _criteria_six():
            above_low = self.get_percent_above_52w_low(ticker, quote)
            if above_low == "error":
                return "error", "error calculating 52wk low"
            elif above_low >= .3:
                return True, above_low
            else:
                return False, above_low

        def _criteria_seven():
            below_high = self.get_percent_below_52w_high(ticker, quote)
            if below_high == "error":
                return "error", "error calculating 52wk high"
            if below_high <= .25:
                return True, below_high
            else:
                return False, below_high


        ticker = ticker.upper()


        if provide_quote is None:
            quote = self.get_stock_quote(ticker)
        else:
            quote = provide_quote

        if check_quote_validity(quote) is False:
            if return_full_details:
                return {"ticker": ticker, "pass": None, "errorFound": True, "error": "Quote Error"}
            else:
                return None
        try:
            mas = self.calculate_moving_average_indicators(ticker)
        except:
            return {"ticker": ticker, "pass": None, "errorFound": True, "error": "MAs calc error"}

        all_history = mas["allHistory"]
        if all_history['empty']:
            return {"ticker": ticker, "pass": None, "errorFound": True, "error": "Quote Error"}
        else:
            candles = all_history['candles']

        current_price = candles[len(candles) - 1]['close']
        current_price = self.get_price(ticker, provided_quote=quote)

        c1 = _criteria_one(current_price, mas)
        c2 = _criteria_two(mas)
        c3, trend_strength_200 = _criteria_three(mas)
        c4 = _criteria_four(mas)
        c5 = _criteria_five(current_price, mas)
        c6, above_52w_low = _criteria_six()
        c7, below_52w_high = _criteria_seven()
        if c1 and c2 and c3 and c4 and c5 and c6 and c7:
            trend_template = True
        else:
            trend_template = False

        if return_full_details:
            rs_value = commonStocksIndicators.ibd_relative_strength(ticker, provided_history=all_history,
                                                                    source_object=self)
            c1_string = None
            c2_string = None
            c3_string = None
            c4_string = None
            c5_string = None
            c6_string = None
            c7_string = None
            c8_string = None

            if include_criteria_descriptions:
                c1_string = "The current stock price is above both the 150-day (30-week) and the 200-day (40-week) " \
                            "moving average price lines."
                c2_string = "The 150-day moving average is above the 200-day moving average."
                c3_string = "The 200-day moving average line is trending up for at least 1 month (preferably 4–5 " \
                            "months minimum in most cases)."
                c4_string = "The 50-day (10-week) moving average is above both the 150-day and 200-day moving averages."
                c5_string = "The current stock price is trading above the 50-day moving average."
                c6_string = "The current stock price is at least 30 percent above its 52-week low. (Many of the best " \
                            "selections will be 100 percent, 300 percent, or greater above their 52-week low before " \
                            "they emerge from a solid consolidation period and mount a large scale advance.)"
                c7_string = "The current stock price is within at least 25 percent of its 52-week high " \
                            "(the closer to a new high the better)."
                c8_string = "The relative strength ranking (as reported in Investor’s Business Daily) is no less " \
                            "than 70, and preferably in the 80s or 90s, which will generally be the case with the " \
                            "better selections."
            return {
                "ticker": ticker,
                "pass": trend_template,
                "errorFound": False,
                "c1": {"pass": c1, "criteria": c1_string},
                "c2": {"pass": c2, "criteria": c2_string},
                "c3": {"pass": c3, "200maTrendStrength": trend_strength_200, "criteria": c3_string},
                "c4": {"pass": c4, "criteria": c4_string},
                "c5": {"pass": c5, "criteria": c5_string},
                "c6": {"pass": c6, "percentAbove52wkLow": above_52w_low, "criteria": c6_string},
                "c7": {"pass": c7, "percentBelow52wkHigh": below_52w_high, "criteria": c7_string},
                "c8": {"pass": "n/a", "criteria": c8_string, "rsValue": rs_value}
            }

        return trend_template


def check_quote_validity(quote):
    """
    Provide the quote and this function returns True if it is valid, False if it is valid
    :param quote:
    :return:
    """
    if type(quote) != dict:
        return False
    else:
        try:
            return not quote["error"]
        except KeyError:
            return False


def order_history_filter_by_ticker(order_history, ticker_filter):
    filtered_history = list()
    applicable_orders_and_legs_after_filters = list()

    ticker = ticker_filter.lower()
    for order in order_history:
        order_id = order["orderId"]
        i = 0
        while i < len(order["orderLegCollection"]):
            if order["orderLegCollection"][i]["instrument"]["symbol"].lower() == ticker:
                filtered_history.append(order.copy())
                applicable_orders_and_legs_after_filters.append({"id": order_id, "leg": i})
            i = i + 1

    return filtered_history, applicable_orders_and_legs_after_filters


def order_history_filter_by_buy_sell(order_history, buy_or_sell):
    filtered_history = list()
    applicable_orders_and_legs_after_filters = list()

    for order in order_history:
        order_id = order["orderId"]
        i = 0
        while i < len(order["orderLegCollection"]):
            if order["orderLegCollection"][i]["instruction"].lower() == buy_or_sell.lower():
                filtered_history.append(order.copy())
                applicable_orders_and_legs_after_filters.append({"id": order_id, "leg": i})
            i = i + 1

    return filtered_history, applicable_orders_and_legs_after_filters


def order_history_get_ticker_from_order(order_dict, leg):
    return order_dict["orderLegCollection"][leg]["instrument"]["symbol"]


def order_history_get_quantity_purchased(order_dict, leg):
    return order_dict["orderActivityCollection"][leg]["quantity"]


def order_history_get_average_price_of_fill(order_dict, leg):
    execution_legs = order_dict["orderActivityCollection"][leg]["executionLegs"]

    total_cost = 0
    total_quantity = 0
    for fill in execution_legs:
        total_quantity = total_quantity + fill["quantity"]
        total_cost = (fill["price"] * fill["quantity"]) + total_cost

    return mC.pretty_round_function(total_cost/total_quantity, 2)


def order_history_get_buy_or_sell(order_dict, leg):
    return order_dict["orderLegCollection"][leg]["instruction"]


def order_history_get_execution_time(order_dict):
    close_time = order_dict['closeTime']
    close_time = tC.convert_time_formats(close_time, "ISO 8601")
    date = close_time["year"] + close_time["month"] + close_time["day"]
    time = tC.convert_twenty_four_time_to_twelve_time(close_time["hour"] + close_time["minute"] + close_time["second"])
    return {"date": date, "time": time}


def order_history_get_total_dollars(order_dict, leg):
    p = order_history_get_average_price_of_fill(order_dict, leg)
    q = order_history_get_quantity_purchased(order_dict, leg)
    return strC.convert_float_to_currency(mC.pretty_round_function(p*q))


def order_history_create_clean_trade_log(order_dict, leg):
    ticker = order_history_get_ticker_from_order(order_dict, leg)
    price = order_history_get_average_price_of_fill(order_dict, leg)
    time_dict = order_history_get_execution_time(order_dict)
    date = time_dict["date"]
    time = time_dict["time"]
    quantity = order_history_get_quantity_purchased(order_dict, leg)
    order_type = order_history_get_buy_or_sell(order_dict, leg)
    if order_type == "BUY_TO_OPEN":
        return {"tradeType": "option"}
    else:
        dollars = order_history_get_total_dollars(order_dict, leg)
        return {"tradeType": "equity",
                "date": date,
                "time": time,
                "ticker": ticker,
                "price": price,
                "quantity": quantity,
                "type": order_type,
                "dollars": dollars,
                "loggedAsClosed": False,
                "closedDate": None,
                "profit": None,
                "remainingShares": None,
                "associatedTrades": None,
                }


def test_function():
    td = Td()


def test_create_watch_list(api):
    api.watch_list_create("basic materials", ["GFI"])


def test_add_to_watch_list(api):
    t.watch_list_add_ticker("basic materials", "VALE")


def test_watch_list_get(api):
    wl = api.watch_list_get("basic materials")


def calculate_pl(t_api):
    # t_api.get_pl_for_ticker_in_time_frame("2022-02-01", "2022-03-29", "NEM")
    stop = 1
    history = t_api.get_order_history("2022-02-01", "2022-03-29", order_type="filled", buy_sell_all="sell")

    for order in history:
        order_collection = order["orderLegCollection"]
        for leg in order_collection:
            if leg["instruction"] == "BUY":
                stock = leg["instrument"]["symbol"]
                quantity = leg["quantity"]

    stop = 1


def get_shared_token():
    return githubCommon.retrieve_json_content_from_file("grindSunday", "stocks", "td_token_path.json")["token"]



if __name__ == '__main__':
    t = Td(add_api_delay=True, keep_cache=True)
    t.generate_new_token_file()
    trend = t.check_mark_minervini_trend_template("mnkd", return_full_details=True, include_criteria_descriptions=True)
    print(trend)

