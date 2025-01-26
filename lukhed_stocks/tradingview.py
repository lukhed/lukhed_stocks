from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC
from lukhed_basic_utils import listWorkCommon as lC
from lukhed_basic_utils import mathCommon as mC
import json


class TradingView:
    def __init__(self):
        self.screener_columns = ["logoid", "name", "close", "change", "volume", "market_cap_basic",
                                 "number_of_employees", "sector", "industry", "Perf.W", "change|1M",
                                 "Perf.YTD", "Perf.Y", "SMA5", "SMA10", "SMA20", "SMA30", "SMA50", "SMA100", "SMA200",
                                 "price_52_week_high", "price_52_week_low", "High.All", "Low.All",
                                 "average_volume_10d_calc", "average_volume_30d_calc", "average_volume_60d_calc",
                                 "average_volume_90d_calc", "Volatility.W", "Volatility.M", "Perf.W", "Perf.1M",
                                 "Perf.3M", "Perf.6M", "description", "type", "subtype", "update_mode", "pricescale",
                                 "minmov", "fractional", "minmove2", "currency", "fundamental_currency_code"]
        
        self.index_lookup = self._get_index_lookup()

    @staticmethod
    def _parse_start_end_dates(date_start, date_end, date_format="%Y%m%d"):
        # Set date range based on inputs
        fnc_c = tC.convert_date_format
        if date_start is None and date_end is None:
            date_start = "19700101"  # super in past to include all data
            date_end = "30000101"  # super in future to include all data
        else:
            if date_start is None:
                date_start = "19700101"
            else:
                date_start = fnc_c(date_start, date_format, '%Y%m%d') if date_format != '%Y%m%d' else date_start

            if date_end is None:
                date_end = "30000101"
            else:
                date_end = fnc_c(date_end, date_format, '%Y%m%d') if date_format != '%Y%m%d' else date_end

        return date_start, date_end

    def _screener_make_request(self, add_filters=None, add_key_pairs_to_data=None, index=None, 
                               primary_listing_only=True):
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

        """
        Define the base_filter
        """

        base_filter = [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund", "structured"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer", "", "etf", "etf,odd", "etf,otc", "etf,cfd", "etn", "reit",
                       "reit,cfd", "trust,reit"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]},
            {"left": "is_primary", "operation": "equal", "right": primary_listing_only},
            {"left": "active_symbol", "operation": "equal", "right": True}
        ]

        if add_filters is None:
            pass
        elif type(add_filters) == dict:
            base_filter.append(add_filters)
        else:
            [base_filter.append(x) for x in add_filters]

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
            "filter": base_filter,
            "options": {"lang": "en"},
            "markets": ["america"],
            "symbols": base_index_filter,
            "columns": self.screener_columns,
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
            "range": [0, 10000]
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

            if add_key_pairs_to_data is None:
                pass
            else:
                if add_key_pairs_to_data is None:
                    pass
                elif type(add_key_pairs_to_data) == dict:
                    data.update(add_key_pairs_to_data)
                else:
                    [data.update(x) for x in add_key_pairs_to_data]

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
    # LIVE SCREENERS
    def screener_new_highs_lows(self, new_high_or_low='high', month_time_frame=12):
        """
        This returns list of stocks on new highs or lows depending on the input. The lists are provided by
        Trading View

        Method of repairing this function.
        1. https://www.tradingview.com/screener/
        2. Ensure you setup the columns to match self.scanner_columns or your desired output
        3. Run the scan with your desired filter
        4. Search in the network log for "scan"
        5. You can see the payload values for the payload tab in the console.

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

    def screener_get_stocks_by_index(self, index, primary_listing_only=True):
        data = self._screener_make_request(index=index, primary_listing_only=primary_listing_only)
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
    

