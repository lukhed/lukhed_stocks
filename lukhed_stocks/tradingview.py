from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC
from lukhed_basic_utils import listWorkCommon as lC
from lukhed_basic_utils import mathCommon as mC
import json


class TradingView:
    def __init__(self):
        self.screener_filter = None
        self.screener_filter2 = None
        self.screener_columns = None

        self._default_screener_columns()
        self._default_screener_filters()
        self.index_lookup = self._get_index_lookup()

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

    def _screener_make_request(self, add_filters=None, index=None):
        # Create a session and set user-agent
        session = rC.create_new_session(add_user_agent=True)

        # Define the request headers
        headers = {
            "authority": "scanner.tradingview.com",
            "method": "POST",
            "path": "/america/scan",
            "scheme": "https",
            "origin": "https://www.tradingview.com",
            "referer": "https://www.tradingview.com/",
            "x-usenewauth": "true",
        }

        if add_filters is not None:
            self.add_screener_filters(add_filters)

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
            "markets": ["america"],
            "symbols": base_index_filter,
            "columns": self.screener_columns,
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
            "range": [0, 25000]
        }

        # Send the POST request
        url = "https://scanner.tradingview.com/america/scan"
        retrieval_time = tC.create_timestamp()
        response = session.post(url, headers=headers, json=payload)

        # Check the response
        if response.status_code == 200:
            data = json.loads(response.text)
            data.update({"error": False, "statusCode": 200})

            # Format the data
            i = 0
            new_data = []
            while i < len(data['data']):
                a = 0
                temp_data = data['data'][i]['d']
                temp_dict = {}
                while a < len(self.screener_columns):
                    temp_dict[self.screener_columns[a]] = temp_data[a]
                    a = a + 1

                new_data.append(temp_dict.copy())
                i = i + 1

            data['data'] = new_data
            data['date'] = retrieval_time[0:8]
            data['retrievalTime'] = retrieval_time

            return data
        else:
            return {"error": True, "statusCode": response.status_code}

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

        if add_filters is None:
            pass
        elif type(add_filters) == dict:
            self.screener_filter.append(add_filters)
        else:
            [self.screener_filter.append(x) for x in add_filters]

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
    
