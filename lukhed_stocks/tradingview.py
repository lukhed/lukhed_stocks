from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC
from lukhed_basic_utils import listWorkCommon as lC
from lukhed_basic_utils import mathCommon as mC
import json
import time


class ScreenerError(RuntimeError):
    """A screener request that did not come back usable.

    Only raised when the TradingView object was constructed with
    raise_on_error=True. The default stays the historical dict-with-an-error-key
    so existing callers are unaffected.
    """

    def __init__(self, message, status_code=None, attempts=None):
        super().__init__(message)
        self.status_code = status_code
        self.attempts = attempts


class TradingView:
    # Retried: rate limiting, and the 5xx family. A 4xx other than 429 means the
    # payload is wrong, and sending it again more slowly will not fix it.
    RETRY_STATUS = (429, 500, 502, 503, 504)

    def __init__(self, market="america", timeout=20, max_retries=3, backoff=1.5,
                 min_interval=0.0, raise_on_error=False):
        """
        :param market:          str(), the scanner to query. "america" is the
                                default and the only one the built-in column and
                                filter defaults are written for -- the crypto,
                                forex and futures scanners use different column
                                vocabularies, so clear and redefine columns
                                explicitly when pointing at one of those.
        :param timeout:         int(), seconds before a request is abandoned.
                                Previously there was none, so a hung socket
                                blocked the caller indefinitely.
        :param max_retries:     int(), total attempts per request.
        :param backoff:         float(), exponential factor between attempts.
                                Retry-After is honoured when the server sends it.
        :param min_interval:    float(), minimum seconds between requests from
                                this object. 0 keeps the historical behaviour;
                                set it when issuing many screens in a loop.
        :param raise_on_error:  bool(), raise ScreenerError instead of returning
                                {"error": True, ...}. Defaults to False to keep
                                the existing contract. Recommended for new code:
                                the error dict has no "data" key, so a caller
                                that does not check it fails later with a
                                KeyError that points at the wrong line.
        """
        self.screener_filter = None
        self.screener_filter2 = None
        self.screener_columns = None

        self.market = market
        self.timeout = timeout
        self.max_retries = max(1, int(max_retries))
        self.backoff = backoff
        self.min_interval = min_interval
        self.raise_on_error = raise_on_error
        self._last_request_at = None

        self._default_screener_columns()
        self._default_screener_filters()
        self.index_lookup = self._get_index_lookup()

    def set_market(self, market):
        """Point this object at a different TradingView scanner.

        The column and filter defaults are the america ones; other scanners
        publish different fields, so call clear_screener_columns() and define
        columns explicitly after switching.
        """
        self.market = market
        return self.market

    @property
    def screener_url(self):
        return f"https://scanner.tradingview.com/{self.market}/scan"

    @staticmethod
    def filter_column_vs_value(left, operation, value):
        """A filter comparing a column against a literal.

        The wire format puts both cases in the same "right" key, so a bare dict
        gives no hint whether "SMA50" is a number or a column name. These two
        helpers make the call site say which was meant.
        """
        return {"left": left, "operation": operation, "right": value}

    @staticmethod
    def filter_column_vs_column(left, operation, right_column):
        """A filter comparing two of the scanner's own columns.

        e.g. filter_column_vs_column("close", "egreater", "SMA50") for
        "price above the 50-day average" -- a comparison the screener supports
        directly.
        """
        return {"left": left, "operation": operation, "right": right_column}

    def _throttle(self):
        if not self.min_interval or self._last_request_at is None:
            return
        wait = self.min_interval - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)

    def _default_screener_columns(self):
        self.screener_columns = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "close",
            "pricescale",
            "minmov",
            "fractional",
            "minmove2",
            "currency",
            "change",
            "volume",
            "relative_volume_10d_calc",
            "market_cap_basic",
            "fundamental_currency_code",
            "price_earnings_ttm",
            "earnings_per_share_diluted_ttm",
            "earnings_per_share_diluted_yoy_growth_ttm",
            "dividends_yield_current",
            "sector.tr",
            "market",
            "sector",
            "AnalystRating",
            "AnalystRating.tr",
            "exchange"
        ]

    def _default_screener_filters(self):
        self.screener_filter = (
            [
                {
                    "left": "is_primary",
                    "operation": "equal",
                    "right": True
                }
            ]
        )

        self.screener_filter2 = (
            {
                    "operator": "and",
                    "operands": [
                                    {
                                        "operation": {
                                            "operator": "or",
                                            "operands": [
                                                {
                                                    "operation": {
                                                        "operator": "and",
                                                        "operands": [
                                                            {
                                                                "expression": {
                                                                    "left": "type",
                                                                    "operation": "equal",
                                                                    "right": "stock"
                                                                }
                                                            },
                                                            {
                                                                "expression": {
                                                                    "left": "typespecs",
                                                                    "operation": "has",
                                                                    "right": [
                                                                        "common"
                                                                    ]
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "operation": {
                                                        "operator": "and",
                                                        "operands": [
                                                            {
                                                                "expression": {
                                                                    "left": "type",
                                                                    "operation": "equal",
                                                                    "right": "stock"
                                                                }
                                                            },
                                                            {
                                                                "expression": {
                                                                    "left": "typespecs",
                                                                    "operation": "has",
                                                                    "right": [
                                                                        "preferred"
                                                                    ]
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "operation": {
                                                        "operator": "and",
                                                        "operands": [
                                                            {
                                                                "expression": {
                                                                    "left": "type",
                                                                    "operation": "equal",
                                                                    "right": "dr"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "operation": {
                                                        "operator": "and",
                                                        "operands": [
                                                            {
                                                                "expression": {
                                                                    "left": "type",
                                                                    "operation": "equal",
                                                                    "right": "fund"
                                                                }
                                                            },
                                                            {
                                                                "expression": {
                                                                    "left": "typespecs",
                                                                    "operation": "has_none_of",
                                                                    "right": [
                                                                        "etf"
                                                                    ]
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "expression": {
                                            "left": "typespecs",
                                            "operation": "has_none_of",
                                            "right": [
                                                "pre-ipo"
                                            ]
                                        }
                                    }
                                ]
            }
        )

    def _fail(self, message, status_code=None, attempts=None):
        if self.raise_on_error:
            raise ScreenerError(message, status_code=status_code, attempts=attempts)
        return {"error": True, "statusCode": status_code,
                "message": message, "attempts": attempts, "data": []}

    def _screener_make_request(self, add_filters=None, index=None,
                               add_key_pairs_to_data=None):
        # Create a session and set user-agent
        session = rC.create_new_session(add_user_agent=True)

        # Define the request headers
        headers = {
            "authority": "scanner.tradingview.com",
            "method": "POST",
            "path": f"/{self.market}/scan",
            "scheme": "https",
            "origin": "https://www.tradingview.com",
            "referer": "https://www.tradingview.com/",
            "x-usenewauth": "true",
        }

        if add_filters is not None:
            self.add_screener_filter_to_filter(add_filters)

        """
        Add any index filters
        """
        base_index_filter = {"query": {"types": []}, "tickers": []}
        if index is not None:
            core_indice_filter = {"groups": [{"type": "index", "values": []}]}
            for_filter = self._parse_index_str(index)
            core_indice_filter["groups"][0]["values"].append(for_filter)
            base_index_filter.update(core_indice_filter)

        payload = {
            "filter": self.screener_filter,
            "filter2": self.screener_filter2,
            "options": {"lang": "en"},
            "markets": [self.market],
            "symbols": base_index_filter,
            "columns": self.screener_columns,
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
            "range": [0, 25000]
        }

        # Send the POST request. Retried on rate limiting and 5xx
        url = self.screener_url
        response = None
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            retrieval_time = tC.create_timestamp()
            try:
                response = session.post(url, headers=headers, json=payload,
                                        timeout=self.timeout)
            except Exception as exc:          # connection reset, DNS, timeout
                last_error = f"{type(exc).__name__}: {exc}"
                response = None
            finally:
                self._last_request_at = time.monotonic()

            if response is not None and response.status_code == 200:
                break

            if response is not None:
                last_error = f"HTTP {response.status_code}"
                if response.status_code not in self.RETRY_STATUS:
                    break                     # a bad payload will stay bad

            if attempt < self.max_retries:
                delay = self.backoff ** (attempt - 1)
                if response is not None:
                    # Honour the server's own pacing when it sends one.
                    try:
                        delay = max(delay, float(response.headers.get("Retry-After", 0)))
                    except (TypeError, ValueError):
                        pass
                time.sleep(delay)

        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else None
            return self._fail(
                f"TradingView {self.market} screener request failed after "
                f"{self.max_retries} attempt(s): {last_error}",
                status_code=status, attempts=self.max_retries)

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            return self._fail(
                f"TradingView returned HTTP 200 with a body that is not JSON: {exc}",
                status_code=200, attempts=self.max_retries)

        if not isinstance(data, dict) or "data" not in data:
            # A 200 with the wrong shape is the failure mode. Treat it as an error rather than as no results.
            return self._fail(
                "TradingView returned HTTP 200 without a `data` key -- the "
                "response shape changed or the request was rejected upstream.",
                status_code=200, attempts=self.max_retries)

        data.update({"error": False, "statusCode": 200})

        # Format the data. Rows arrive as positional arrays aligned to the
        # columns that were requested, so this zip is order-sensitive.
        new_data = []
        for row in data['data']:
            temp_data = row['d']
            temp_dict = {}
            for a in range(len(self.screener_columns)):
                temp_dict[self.screener_columns[a]] = temp_data[a]
            new_data.append(temp_dict.copy())

        data['data'] = new_data
        data['date'] = retrieval_time[0:8]
        data['retrievalTime'] = retrieval_time

        if add_key_pairs_to_data:
            # Accepts a dict, or the tuple-of-dicts shape the new-high/low
            # screener has always passed.
            pairs = ([add_key_pairs_to_data]
                     if isinstance(add_key_pairs_to_data, dict)
                     else list(add_key_pairs_to_data))
            for pair in pairs:
                data.update(pair)

        return data

    def _parse_index_str(self, index_str):
        index_str = index_str.lower()

        try:
            return self.index_lookup[index_str]
        except KeyError:
            print(f"ERROR: {index_str} is not a valid index filter. Check self.index_lookup for supported inputs.")
            return None
    
    @staticmethod
    def _get_index_lookup():
        return {
            "dow": "DJ:DJI",                                    # Down Jowns Industrial average (30 stocks)
            "nasdaq": "NASDAQ:IXIC",                            # Nasdaq Composite (all stocks in nasdaq)
            "nasdaq 100": "NASDAQ:NDX",                         # Nasdaq 100 (~100 stocks)
            "nasdaq bank": "NASDAQ:BANK",
            "nasdaq biotech": "NASDAQ:NBI",
            "nasdaq computer": "NASDAQ:IXCO",
            "nasdaq industrial": "NASDAQ:INDS",
            "nasdaq insurance": "NASDAQ:INSR",
            "nasdaq other finance": "NASDAQ:OFIN",
            "nasdaq telecommunications": "NASDAQ:IXTC",
            "nasdaq transportation": "NASDAQ:TRAN",
            "nasdaq food producers": "NASDAQ:NQUSB451020",
            "nasdaq golden dragon": "NASDAQ:HXC",
            "s&p": "SP:SPX",                                    # S&P 500 (~500 stocks)
            "s&p communication services": "SP:S5TELS",
            "s&p consumer discretionary": "SP:S5COND",
            "s&p consumer staples": "SP:S5CONS",
            "s&p energy": "SP:SPN",
            "s&p financials": "SP:SPF",
            "s&p healthcare": "SP:S5HLTH",
            "s&p industrials": "SP:S5INDU",
            "s&p it": "SP:S5INFT",
            "s&p materials": "SP:S5MATR",
            "s&p real estate": "SP:S5REAS",
            "s&p utilities": "SP:S5UTIL",
            "russel 2000": "TVC:RUT"                            # Russel 2000
        }


    #####################
    # SCREENER SETTINGS
    def add_screener_filter_to_filter(self, add_filters):
        """
        This function will add filters to filter. All screens performed after running the add will 
        have the additional filters.

        :param add_filters:        dict() or list(). Provide the filter(s) to add to the base screener filter.
        :return:                    None
        """
        if self.screener_filter is None:
            self.screener_filter = []

        if add_filters is None:
            pass
        elif type(add_filters) == dict:
            self.screener_filter.append(add_filters)
        else:
            [self.screener_filter.append(x) for x in add_filters]

        if self.screener_filter == []:
            self.screener_filter = None

    def reset_screener_filters(self):
        """
        This function will reset the screener filters to the default settings.

        :return: None
        """

        self._default_screener_filters()

    def clear_screener_filters(self):
        """
        This function will clear all screener filters.

        Note: This will combine stock types and other types. The website uses filters to separate the screeners 
        (e.g., ETF and stocks) and this function removes all filters.

        :return: None
        """

        self.screener_filter = None
        self.screener_filter2 = None

    def set_custom_screener_filter(self, custom_filter):
        """
        This function will set the screener filter (filter) to match the input list. 

        :param custom_filter:       dict() or list(). Check TradingView requests payload for filter structure.

        :return: None
        """

        self.clear_screener_filters()

        self.screener_filter = custom_filter

    def set_custom_screener_filter2(self, custom_filter):
        """
        This function will set the screener filter2 to match the input list. Check TradingView requests
        payload for filter structure.

        :param custom_filter:        dict() or list(). Check TradingView requests payload for filter structure.
        """

        self.clear_screener_filters()

        self.screener_filter2 = custom_filter

        
    #####################
    # COLUMN SETTINGS
    def _set_screener_columns(self, add_bool, column_list):
        if not add_bool:
            self.clear_screener_columns()

        for column in column_list:
            if column not in self.screener_columns:
                self.screener_columns.append(column)

    def reset_screener_columns(self):
        """
        This function will reset the screener columns to the default settings.

        :return: None
        """

        self._default_screener_columns()

    def clear_screener_columns(self):
        """
        This function will clear all screener columns except for symbol.

        :return: None
        """

        self.screener_columns = ["name"]

    def custom_define_columns(self, column_list, add_to_current_columns=False):
        """
        This function will set the screener columns to match the input list.

        :param column_list:        list(). Provide a list of screener columns to use in the screener.

        :return: None
        """

        self._set_screener_columns(add_to_current_columns, column_list)

    def set_stock_screener_columns_time_period_performance(self, add_to_current_columns=False):
        """
        This function will add all market performance % data to the default screen columns. All screens performed 
        after running the add will have all the information.
        """
        all_perf_columns = [
            "Perf.W",
            "Perf.1M",
            "Perf.3M",
            "Perf.6M",
            "Perf.Y",
            "Perf.5Y",
            "Perf.10Y",
            "Perf.All",
        ]

        self._set_screener_columns(add_to_current_columns, all_perf_columns)
    
    def set_stock_screener_columns_overview(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock overview tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "close",
            "pricescale",
            "minmov",
            "fractional",
            "minmove2",
            "currency",
            "change",
            "volume",
            "relative_volume_10d_calc",
            "market_cap_basic",
            "fundamental_currency_code",
            "price_earnings_ttm",
            "earnings_per_share_diluted_ttm",
            "earnings_per_share_diluted_yoy_growth_ttm",
            "dividends_yield_current",
            "sector.tr",
            "market",
            "sector",
            "AnalystRating",
            "AnalystRating.tr",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    def set_stock_screener_columns_performance(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock performance tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "close",
            "pricescale",
            "minmov",
            "fractional",
            "minmove2",
            "currency",
            "change",
            "Perf.W",
            "Perf.1M",
            "Perf.3M",
            "Perf.6M",
            "Perf.YTD",
            "Perf.Y",
            "Perf.5Y",
            "Perf.10Y",
            "Perf.All",
            "Volatility.W",
            "Volatility.M",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    def set_stock_screener_columns_extended_hours(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock extended hours tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "premarket_close",
            "pricescale",
            "minmov",
            "fractional",
            "minmove2",
            "currency",
            "premarket_change",
            "premarket_gap",
            "premarket_volume",
            "close",
            "change",
            "gap",
            "volume",
            "volume_change",
            "postmarket_close",
            "postmarket_change",
            "postmarket_volume",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    def set_stock_screener_columns_valuation(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock valuation tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "market_cap_basic",
            "fundamental_currency_code",
            "Perf.1Y.MarketCap",
            "price_earnings_ttm",
            "price_earnings_growth_ttm",
            "price_sales_current",
            "price_book_fq",
            "price_to_cash_f_operating_activities_ttm",
            "price_free_cash_flow_ttm",
            "price_to_cash_ratio",
            "enterprise_value_current",
            "enterprise_value_to_revenue_ttm",
            "enterprise_value_to_ebit_ttm",
            "enterprise_value_ebitda_ttm",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    def set_stock_screener_columns_dividends(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock dividends tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "dps_common_stock_prim_issue_fy",
            "fundamental_currency_code",
            "dps_common_stock_prim_issue_fq",
            "dividends_yield_current",
            "dividends_yield",
            "dividend_payout_ratio_ttm",
            "dps_common_stock_prim_issue_yoy_growth_fy",
            "continuous_dividend_payout",
            "continuous_dividend_growth",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    def set_stock_screener_columns_profitiability(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock profitability tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "gross_margin_ttm",
            "operating_margin_ttm",
            "pre_tax_margin_ttm",
            "net_margin_ttm",
            "free_cash_flow_margin_ttm",
            "return_on_assets_fq",
            "return_on_equity_fq",
            "return_on_invested_capital_fq",
            "research_and_dev_ratio_ttm",
            "sell_gen_admin_exp_other_ratio_ttm",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    def set_stock_screener_columns_per_share(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock per share tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "revenue_per_share_ttm",
            "fundamental_currency_code",
            "earnings_per_share_basic_ttm",
            "earnings_per_share_diluted_ttm",
            "operating_cash_flow_per_share_ttm",
            "free_cash_flow_per_share_ttm",
            "ebit_per_share_ttm",
            "ebitda_per_share_ttm",
            "book_value_per_share_fq",
            "total_debt_per_share_fq",
            "cash_per_share_fq",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    def set_stock_screener_columns_technicals(self, add_to_current_columns=False):
        """
        This function will set the screener columns to match the stock technicals tab on TradingView.

        :return: None
        """

        self.clear_screener_columns()
        columns_to_add = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "TechRating_1D",
            "TechRating_1D.tr",
            "MARating_1D",
            "MARating_1D.tr",
            "OsRating_1D",
            "OsRating_1D.tr",
            "RSI",
            "Mom",
            "pricescale",
            "minmov",
            "fractional",
            "minmove2",
            "AO",
            "CCI20",
            "Stoch.K",
            "Stoch.D",
            "Candle.3BlackCrows",
            "Candle.3WhiteSoldiers",
            "Candle.AbandonedBaby.Bearish",
            "Candle.AbandonedBaby.Bullish",
            "Candle.Doji",
            "Candle.Doji.Dragonfly",
            "Candle.Doji.Gravestone",
            "Candle.Engulfing.Bearish",
            "Candle.Engulfing.Bullish",
            "Candle.EveningStar",
            "Candle.Hammer",
            "Candle.HangingMan",
            "Candle.Harami.Bearish",
            "Candle.Harami.Bullish",
            "Candle.InvertedHammer",
            "Candle.Kicking.Bearish",
            "Candle.Kicking.Bullish",
            "Candle.LongShadow.Lower",
            "Candle.LongShadow.Upper",
            "Candle.Marubozu.Black",
            "Candle.Marubozu.White",
            "Candle.MorningStar",
            "Candle.ShootingStar",
            "Candle.SpinningTop.Black",
            "Candle.SpinningTop.White",
            "Candle.TriStar.Bearish",
            "Candle.TriStar.Bullish",
            "exchange"
        ]

        self._set_screener_columns(add_to_current_columns, columns_to_add)

    #####################
    # LIVE SCREENERS
    def screener_new_highs_lows(self, new_high_or_low='high', month_time_frame=12):
        """
        This returns list of stocks on new highs or lows depending on the input. The lists are provided by
        TradingView.

        :param new_high_or_low:         str(), Define the screener to get high or low.

        :param month_time_frame:        str(), Define the screener to get new 1, 3, 6, or 12 month highs. "all time"
                                        is also supported for all time highs or lows

        :return:                        dict(), with a list of stocks meeting the screen definition. All stocks
                                        will come with meta data defined in self.scanner_columns
        """

        if month_time_frame == 'all time':
            filter_key = 'at'
        else:
            filter_key = int(month_time_frame)

        filters = {
            "high": {1: {"left": "High.1M", "operation": "eless", "right": "high"},
                     3: {"left": "High.3M", "operation": "eless", "right": "high"},
                     6: {"left": "High.6M", "operation": "eless", "right": "high"},
                     12: {"left": "price_52_week_high", "operation": "eless", "right": "high"},
                     "at": {"left": "High.All", "operation": "eless", "right": "high"}
                     },
            "low": {1: {"left": "Low.1M", "operation": "egreater", "right": "low"},
                    3: {"left": "Low.3M", "operation": "egreater", "right": "low"},
                    6: {"left": "Low.6M", "operation": "egreater", "right": "low"},
                    12: {"left": "price_52_week_low", "operation": "egreater", "right": "low"},
                    "at": {"left": "Low.All", "operation": "egreater", "right": "low"}
                    }
        }

        add_filter = filters[new_high_or_low][filter_key]
        add_key_pairs_to_data = {"timeframe": month_time_frame}, {"highOrLow": new_high_or_low.lower()}

        data = self._screener_make_request(add_filters=add_filter, add_key_pairs_to_data=add_key_pairs_to_data)

        return data

    def screener_get_all_stocks(self):
        data = self._screener_make_request()
        return data

    def screener_get_stocks_by_index(self, index):
        """
        Get stocks by index. Use index lookup to see supported index inputs.
        :param index:                   str(), Provide the index name to filter stocks by. All options in 
                                        self.index_lookup. Common options are: "dow", "nasdaq", "s&p", "russel 2000"
        :param primary_listing_only:    bool(), If true, only return stocks that are primary
        """

        data = self._screener_make_request(index=index)
        return data

    #####################
    # STOCK LIST FILTERS AND FUNCTIONS.
    def filter_stock_list_by_sector(self, sectors, stock_list):
        """
        Returns a list of stocks that meet the sector criteria provided.

        :param sectors:             str() or list(). Provide the name of the sectors you want in your output.
        :param stock_list:          list(), list of TradingView stock dicts()
        :return:
        """

        if sectors is None:
            return stock_list
        elif type(sectors) is str:
            sectors = sectors.lower()
            return [x for x in stock_list if (x['sector'] is not None and x['sector'].lower() == sectors)]
        else:
            sectors = [x.lower() for x in sectors]
            return [x for x in stock_list if (x['sector'].lower() in sectors)]

    def filter_stock_list_by_industry(self, industries, stock_list):
        """
        Returns a list of stocks that meet the sector criteria provided.

        :param industries:          str() or list(). Provide the name of the sectors you want in your output.
        :param stock_list:          list(), list of TradingView stock dicts()
        :return:
        """

        if industries is None:
            return stock_list
        elif type(industries) is str:
            industries = industries.lower()
            return [x for x in stock_list if (x['industry'] is not None and x['industry'].lower() == industries)]
        else:
            industries = [x.lower() for x in industries]
            return [x for x in stock_list if (x['industry'] is not None and x['industry'].lower() in industries)]

    def get_all_industries_in_list(self, stock_list):
        return lC.return_unique_values([x['industry'] for x in stock_list])

    def get_all_sectors_in_list(self, stock_list):
        return lC.return_unique_values([x['sector'] for x in stock_list])

    def get_sector_industry_breakdown_of_list(self, stock_list):
        sectors = self.get_all_sectors_in_list(stock_list)
        industries = self.get_all_industries_in_list(stock_list)

        op = []
        for s in sectors:
            count = len([x for x in stock_list if x['sector'] == s])
            fraction = mC.pretty_round_function(count/len(stock_list), 4)
            op.append({
                "type": "sector",
                "name": s,
                "count": count,
                "fraction": fraction
            })

        for i in industries:
            count = len([x for x in stock_list if x['industry'] == i])
            fraction = mC.pretty_round_function(count / len(stock_list), 4)
            op.append({
                "type": "industry",
                "name": i,
                "count": count,
                "fraction": fraction
            })

        return op

    def get_unique_stock_tickers_in_list(self, stock_list):
        tickers = [x['name'] for x in stock_list]
        return lC.return_unique_values(tickers)
    
