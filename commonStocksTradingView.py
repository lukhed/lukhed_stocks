from lukhed_basic_utils import osCommon as osC
from lukhed_basic_utils import fileCommon as fC
from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC
from lukhed_basic_utils import listWorkCommon as lC
from lukhed_basic_utils import mathCommon as mC
import re
from typing import Optional
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
        self.index_lookup = {
            "dow": "DJ:DJI",  # Down Jowns Industrial average (30 stocks)
            "nasdaq": "NASDAQ:IXIC",  # Nasdaq Composite (all stocks in nasdaq)
            "nasdaq 100": "NASDAQ:NDX",  # Nasdaq 100 (~100 stocks)
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
            "s&p": "SP:SPX",  # S&P 500 (~500 stocks)
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
            "russel 2000": "TVC:RUT"  # Russel 2000
        }
        self.archive = []                       # Archive with all the list information from various files
        self.archive_stock_list = []            # Just the stock list deriving from the archive
        self.archive_dir = None

    def _parse_provided_archive_input(self, provide_archive_input):
        if provide_archive_input is None:
            return self.archive
        else:
            return provide_archive_input

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

    def _screener_make_request(self, add_filters=None, add_key_pairs_to_data=None, index=None):
        # Create a session and set user-agent
        session = rC.create_new_session(add_user_agent="yes")

        # Define the request headers
        headers = {
            "authority": "scanner.tradingview.com",
            "method": "POST",
            "path": "/america/scan",
            "scheme": "https",
            "accept": "text/plain, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.tradingview.com",
            "referer": "https://www.tradingview.com/",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
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
            {"left": "is_primary", "operation": "equal", "right": True},
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
        retrieval_time = tC.create_time_stamp_new()
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

    #####################
    # HIGH LOW ARCHIVE FUNCTIONS
    def load_high_low_archive(self, archive_location='default', date_start=None, date_end=None,
                              provided_date_format="%Y%m%d", last_x_available=None, last_from_date=None,
                              high_low_both='both', period_include_list=None, sort_archive_by_date=False):
        """
        Use the parameters to load the high low archive. Two methods to load data: providing dates or providing an
        integer via the last_x_available parameter. See the details below.

        :param archive_location:            str(), path to high low archive. If 'default' will use self.archive_dir

        :param date_start:                  str(), method 1 parameter used by not providing last_x_available:
                                                   Set the start date inclusive. If using this method and left blank,
                                                   date start will be set before data is available (infinte in past).
                                                   If using last_x_available, this parameter is ignored.

        :param date_end:                    str(), method 1 parameter used by not providing last_x_available:
                                                   Set the end date inclusive. If using this method and left blank,
                                                   date end will be set for today's date. If using last_x_available,
                                                   this parameter is ignored.

        :param provided_date_format:        str(), method 1 parameter, provide the date format you are using

        :param period_include_list:         str(), list of periods to include in the data (12m, 6m, 3m, 1m)

        :param last_x_available:            int(), method 2 parameter. Will return the last x days available in the
                                                   archive or x days from the 'last_from_date'. If you set this
                                                   parameter then the method 1 parameters will be ignored.

                                                   NOTE: given the nature of the archive (it is logged on trading days),
                                                   x is not days from today, x is last x trading days that were logged.
                                                   If you need exact date precision, use method 1.

        :param last_from_date:              str(), method 2 parameter. Sets the start date to start calculating the
                                                   last_x_available from.

        :param high_low_both:               str(), 'high', 'low', or 'both'.

        :param sort_archive_by_date:
        :return:
        """

        self._parse_archive_location(archive_location)

        if last_x_available is None:
            date_start, date_end = self._parse_start_end_dates(date_start, date_end, provided_date_format)

        loc = self.archive_dir
        all_files = []
        if period_include_list is None:
            period_criteria = [1, 3, 6, 12]
        else:
            period_criteria = [int(x) for x in period_include_list]

        if high_low_both == 'both':
            price_type_criteria = ['High', 'Low']
        else:
            price_type_criteria = high_low_both.capitalize()

        get_files = osC.return_files_in_dir_as_strings
        if 'High' in price_type_criteria:
            if 1 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '1mHigh'), full_path=True))
            if 3 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '3mHigh'), full_path=True))
            if 6 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '6mHigh'), full_path=True))
            if 12 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '52wkHigh'), full_path=True))

        if 'Low' in price_type_criteria:
            if 1 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '1mLow'), full_path=True))
            if 3 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '3mLow'), full_path=True))
            if 6 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '6mLow'), full_path=True))
            if 12 in period_criteria:
                all_files.extend(get_files(osC.append_to_dir(loc, '52wkLow'), full_path=True))


        # Filter dates out:
        fnc_get_fn = osC.extract_file_name_given_full_path
        fnc_check_time = tC.check_if_date_time_string_is_in_given_range
        if last_x_available is None:
            all_files = [x for x in all_files if
                         fnc_check_time(fnc_get_fn(x).split("_")[1].replace(".json", "")[0:8], date_start, date_end,
                                        "%Y%m%d")]
        else:
            temp_dates = [fnc_get_fn(x).split("_")[1].replace(".json", "")[:8] for x in all_files]
            unique_dates = lC.return_unique_values(temp_dates)
            unique_dates.sort(reverse=True)
            if last_from_date is not None:
                last_from_date = tC.convert_date_format(last_from_date, provided_date_format, "%Y%m%d")
                start_index = unique_dates.index(last_from_date)
                unique_dates = unique_dates[start_index:]

            criteria_dates = [x for x in unique_dates[:last_x_available]]
            all_files = [x for x in all_files if fnc_get_fn(x).split("_")[1].replace(".json", "")[:8] in criteria_dates]

        self.archive = [fC.load_json_from_file(x) for x in all_files]

        if sort_archive_by_date:
            self.archive = self.sort_archive_by_date()

        for archive_item in self.archive:
            self.archive_stock_list.extend(archive_item['data'])

        return self.archive

    def sort_archive_by_date(self, provide_archive_data=None):
        archive = self._parse_provided_archive_input(provide_archive_data)
        dates = [tC.convert_date_to_date_time(x['date']) for x in archive]
        sorted_archive = lC.new_sort_list_based_on_reference_list(dates, archive)
        sorted_archive.reverse()
        return sorted_archive


    def search_high_low_archive(self, date_start=None, date_end=None, provided_date_format="%Y%m%d",
                                timeframe=None, high_or_low=None, sectors=None, industries=None,
                                provide_archive_data=None):
        """
        This function returns a list of stocks that meet the criteria. Must load archive first via
        load_high_low_archive or provide data via provide_archive_data.

        :param date_start:                  str(), start date (inclusive) you want results for. If you leave it None,
                                            all dates up to date_end will be included. If you
                                            only want one day to be included, set the date_end parameter equal to
                                            the date_start.

        :param date_end:                    str(), end date (inclusive) you want results for. If you leave it None,
                                            all dates that are available in the archive starting with date_start
                                            and going infintely in the future will be included.

        :param provided_date_format:        str(), format of the date stgring you are providing in the date_start
                                            and date_end parameters.

        :param timeframe:                   int(), The high_low list archive contains the following options:
                                            1 = 1month high/low
                                            3 = 3month high/low
                                            6 = 6month high/low
                                            12 = 12month high/low

                                            Leaving it None returns all timeframes

        :param high_or_low:                 str(), 'high' or 'low'. Leaving it None will return both.

        :param sectors:                     str() or list(). Provide the name of the sectors you want in your output

        :param industries:                  str() or list(). Provide the name(s) of the industries you want in your
                                            output

        :param provide_archive_data:        dict(), archive data dict that is the type of this function
                                            (see load_high_low_archive)
        :return:
        """

        working = self._filter_high_low_archive_by_date_range(date_start, date_end, provided_date_format,
                                                              provide_archive_data)
        working = self._filter_high_low_archive_by_timeframe(timeframe, working)
        working = self._filter_high_low_archive_by_high_low(high_or_low, working)

        all_stocks = []
        for applicable_archive in working:
            all_stocks.extend(applicable_archive['data'])

        all_stocks = self.filter_stock_list_by_sector(sectors, all_stocks)
        all_stocks = self.filter_stock_list_by_industry(industries, all_stocks)

        return all_stocks

    def get_most_recent_data_for_stock_in_archive(self, ticker, provide_archive_data=None):
        archive = self.sort_archive_by_date(provide_archive_data=provide_archive_data)
        sorted_one_month = [x for x in archive if x['timeframe'] == 1]

        ticker = ticker.upper()
        date_found = None
        stock_found = None

        for a in sorted_one_month:
            if date_found is not None:
                break
            for stock in a['data']:
                if stock['name'] == ticker:
                    date_found = a['date']
                    stock_found = stock
                    break

        return {"mostRecentOccurrence": date_found, "stock": stock_found}

    @staticmethod
    def get_last_x_days_available_in_high_low_archive(archive_location='default', last_x_days='all',
                                                      return_date_format="%Y%m%d"):
        """
        Returns a list of the last 5 days available in the high low archive.

        :param last_x_days:             str() or int(), 'all' will return all dates in archive. 5 will return
                                        last five available.
        :param archive_location:

        :param return_date_format:
        :return:
        """
        if archive_location == 'default':
            loc = osC.create_file_path_string(['resources', 'grindSundayStocks', 'high-low-lists'])
        else:
            loc = archive_location

        dirs = osC.return_files_in_dir_as_strings(loc, full_path=True)
        all_dates = []
        for d in dirs:
            all_dates.extend(osC.return_files_in_dir_as_strings(d))

        all_dates = [tC.convert_date_format(re.search(r'_(\d+)', x).group(1), "%Y%m%d%H%M%S",
                                            return_date_format) for x in all_dates]
        all_dates = lC.return_unique_values(all_dates)

        if last_x_days == "all":
            return all_dates
        else:
            return all_dates[-last_x_days:]

    def load_indice_archive(self, indice, archive_location='default', date_start=None, date_end=None,
                            provided_date_format="%Y%m%d"):
        """
        This function will load all indice history from the logs in the provided archive_location

        :param indice:                  str(), currently supported:
                                            's&p' - loads all s&p related archive data including sectors

        :param archive_location:        str(), default assumes running from grindSundayStocks. Else provide the full
                                        path to the folder 'indice-logs' which has the raw data.

        :param date_start:
        :param date_end:
        :param provided_date_format:
        :return:
        """

        if archive_location == 'default':
            archive = osC.create_file_path_string(['resources', 'grindSundayStocks', 'indice-logs'])
        else:
            archive = archive_location

        date_start, date_end = self._parse_start_end_dates(date_start, date_end, provided_date_format)

        indice = indice.lower()

        hash_select = {
            "s&p": {
                "full_index": 'logsp500',
                "communication_services": 'logspcommservices',
                "consumer_discretionary": 'logspconsumerdiscretionary',
                'consumer_staples': 'logspconsumerstaples',
                'energy': 'logspenergy',
                'financials': 'logspfinancials',
                'healthcare': 'logsphealthcare',
                'industrials': 'logspindustrials',
                'information_technology': 'logspit',
                'materials': 'logspmaterials',
                'real_estate': 'logsprealestate',
                'utilities': 'logsputilities'
            }
        }

        op_data = {}
        for k in hash_select[indice]:
            op_data[k] = []
            temp_dir = osC.append_to_dir(archive, hash_select[indice][k])
            temp_files = osC.return_files_in_dir_as_strings(temp_dir, full_path=True)
            for f in temp_files:
                date_to_check = osC.extract_file_name_given_full_path(f).split("_")[1][0:8]
                if tC.check_if_date_time_string_is_in_given_range(date_to_check, date_start, date_end, "%Y%m%d"):
                    op_data[k].append(fC.load_json_from_file(f))

        self.archive = op_data

        return self.archive

    def get_industry_list_from_archive(self, provide_archive=None):
        """
        Returns the uniqe list of industries in a given archive

        :param provide_archive:
        :return:
        """
        archive = self._parse_provided_archive_input(provide_archive)

        industry_list = []
        for archive_item in archive:
            [industry_list.append(x['industry']) for x in archive_item['data']]

        return lC.return_unique_values(industry_list)

    def get_sector_list_from_archive(self, provide_archive=None):
        """
        Returns the unique list of sectors in a given archive.

        :param provide_archive:
        :return:
        """
        archive = self._parse_provided_archive_input(provide_archive)

        industry_list = []
        for archive_item in archive:
            [industry_list.append(x['sector']) for x in archive_item['data']]

        return lC.return_unique_values(industry_list)

    def get_archive_statistics(self, provide_archive=None):
        """
        Returns a dict with basic statistics about the current archive. For example, sector and industry counts.
        By default it uses the currently loaded archive. You can load an archive with load functions like
        "load_high_low_archive" or "load_indice_archive".

        :param provide_archive:
        :return:
        """

        archive = self._parse_provided_archive_input(provide_archive)
        unique_sector_list = self.get_sector_list_from_archive(provide_archive=archive)
        unique_ind_list = self.get_industry_list_from_archive(provide_archive=archive)

        all_sector_list = [x['sector'] for x in self.archive_stock_list]
        all_industry_list = [x['industry'] for x in self.archive_stock_list]

        sector_data = [{x: all_sector_list.count(x)} for x in unique_sector_list]
        industry_data = [{x: all_industry_list.count(x)} for x in unique_ind_list]

        return {"sectorData": sector_data, "industryData": industry_data}


    def _filter_high_low_archive_by_date_range(self, date_start, date_end, provided_format="%Y%m%d",
                                               provide_archive=None):
        archive = self._parse_provided_archive_input(provide_archive)

        # Set date range based on inputs
        if date_start is None and date_end is None:
            return archive
        else:
            if date_start is None:
                date_start = "19700101"

            if date_end is None:
                date_end = "30000101"

        # Convert dates to correct format
        fnc_cd = tC.convert_date_format
        sd = fnc_cd(date_start, provided_format, "%Y%m%d") if provided_format != "%Y%m%d" else date_start
        ed = fnc_cd(date_end, provided_format, "%Y%m%d") if provided_format != "%Y%m%d" else date_end

        # check if date is in range
        fnc_range = tC.check_if_date_time_string_is_in_given_range
        return [x for x in archive if fnc_range(x['date'], sd, ed, input_format="%Y%m%d")]

    def _filter_high_low_archive_by_timeframe(self, timeframe, provide_archive=None):
        archive = self._parse_provided_archive_input(provide_archive)

        if timeframe is None:
            return archive
        else:
            return [x for x in archive if x['timeframe'] == timeframe]

    def _filter_high_low_archive_by_high_low(self, high_or_low, provide_archive=None):
        archive = self._parse_provided_archive_input(provide_archive)

        if high_or_low is None:
            return archive
        else:
            return [x for x in archive if x['highOrLow'] == high_or_low.lower()]

    def _parse_archive_location(self, archive_location):
        if archive_location == 'default':
            self.archive_dir = osC.create_file_path_string(['resources', 'grindSundayStocks', 'high-low-lists'])
        else:
            self.archive_dir = archive_location

    #####################
    # LIVE SCREENERS
    def screener_new_highs_lows(self, new_high_or_low='high', month_time_frame=12):
        """
        This returns list of stocks on new highs or lows depending on the input. The lists are provided by
        Trading View

        Method of reparing this function.
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

    def screener_get_stocks_by_index(self, index):
        data = self._screener_make_request(index=index)
        return data

    #####################
    # STOCK LIST FILTERS AND FUNCTIONS. These will perform on Archive by default unless stock list is provided.
    def _parse_stock_list_input(self, stock_list):
        if stock_list is None:
            return self.archive_stock_list
        else:
            return stock_list

    def filter_stock_list_by_sector(self, sectors, stock_list=None):
        """
        Returns a list of stocks that meet the sector criteria provided. By default this function will use the
        self.archive_stock_list unless a stock_list is provided. To use the default functionality, you need to first
        load an archive.

        :param sectors:             str() or list(). Provide the name of the sectors you want in your output.
        :param stock_list:          list(), list of TradingView stock dicts()
        :return:
        """
        stock_list = self._parse_stock_list_input(stock_list)

        if sectors is None:
            return stock_list
        elif type(sectors) is str:
            sectors = sectors.lower()
            return [x for x in stock_list if (x['sector'] is not None and x['sector'].lower() == sectors)]
        else:
            sectors = [x.lower() for x in sectors]
            return [x for x in stock_list if (x['sector'].lower() in sectors)]

    def filter_stock_list_by_industry(self, industries, stock_list=None):
        """
        Returns a list of stocks that meet the sector criteria provided.  By default this function will use the
        self.archive_stock_list unless a stock_list is provided. To use the default functionality, you need to first
        load an archive.

        :param industries:             str() or list(). Provide the name of the sectors you want in your output.
        :param stock_list:          list(), list of TradingView stock dicts()
        :return:
        """

        stock_list = self._parse_stock_list_input(stock_list)

        if industries is None:
            return stock_list
        elif type(industries) is str:
            industries = industries.lower()
            return [x for x in stock_list if (x['industry'] is not None and x['industry'].lower() == industries)]
        else:
            industries = [x.lower() for x in industries]
            return [x for x in stock_list if (x['industry'] is not None and x['industry'].lower() in industries)]

    def get_all_industries_in_list(self, stock_list=None):
        stock_list = self._parse_stock_list_input(stock_list)
        return lC.return_unique_values([x['industry'] for x in stock_list])

    def get_all_sectors_in_list(self, stock_list=None):
        stock_list = self._parse_stock_list_input(stock_list)
        return lC.return_unique_values([x['sector'] for x in stock_list])

    def get_sector_industry_breakdown_of_list(self, stock_list=None):
        stock_list = self._parse_stock_list_input(stock_list)
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

    def get_unique_stock_tickers_in_list(self, stock_list=None):
        stock_list = self._parse_stock_list_input(stock_list)
        tickers = [x['name'] for x in stock_list]
        return lC.return_unique_values(tickers)


def get_test_resource_loc():
    drive_letter = osC.create_root_path_starting_from_drive("C:")
    d = ["Users", 'heide', "Documents", "Luke", "Programming", 'grindSundayStocks', 'resources', 'grindSundayStocks']

    return osC.append_to_dir(drive_letter, d, list=True)


def test_get_all_stocks_in_high_low_archive_for_week():
    tv = TradingView()
    resource_dir = get_test_resource_loc()
    archive_loc = osC.append_to_dir(resource_dir, 'high-low-lists')
    tv.load_high_low_archive(archive_location=archive_loc)
    current_week = tC.get_week_bounds_given_week_number(tC.get_week_number_for_current_date())
    week_archive = tv.search_high_low_archive(date_start=current_week['monday'], date_end=current_week['sunday'])
    stop = 1


def test_indice_archive():
    tv = TradingView()
    resource_dir = get_test_resource_loc()
    archive_loc = osC.append_to_dir(resource_dir, 'indice-logs')
    indice_archive = tv.load_indice_archive('s&p', archive_location=archive_loc)

    total_stocks_in_indice = indice_archive['full_index'][0]['totalCount']
    total_stocks_in_sub_indices = sum([indice_archive[x][0]['totalCount'] for x in indice_archive if x != 'full_index'])

    full_indice_stocks = [x['name'] for x in indice_archive['full_index'][0]['data']]
    sub_indice_stocks = []
    [sub_indice_stocks.extend(indice_archive[x][0]['data']) for x in indice_archive if x != 'full_index']
    sub_indice_stocks = [x['name'] for x in sub_indice_stocks]
    full_indice_stocks.sort()
    sub_indice_stocks.sort()

    unique_stocks_in_full_indice = [x for x in full_indice_stocks if x not in sub_indice_stocks]
    unique_stocks_in_sub_indices = [x for x in sub_indice_stocks if x not in full_indice_stocks]

    stop = 1


def test_high_low_screener():
    tv = TradingView()
    year_highs = tv.screener_new_highs_lows()
    stop = 1


def test_get_all_stocks_screener():
    tv = TradingView()
    all_stocks = tv.screener_get_all_stocks()
    stop = 1


def test_base_screener_function():
    tv = TradingView()
    dow = tv._screener_make_request(index="s&p financials")
    stop = 1


def test_get_stocks_by_index_screener():
    tv = TradingView()
    nasdaq = tv.screener_get_stocks_by_index('nasdaq')
    stop = 1


def test_get_all_industries_in_list():
    tv = TradingView()
    all_stocks = tv.screener_get_all_stocks()
    industries = tv.get_all_industries_in_list(stock_list=all_stocks['data'])
    stop = 1


def test_get_last_x_days_available_in_high_low_archive():
    res_dir = get_test_resource_loc()
    test_loc = osC.append_to_dir(res_dir, "high-low-lists")

    tv = TradingView()
    t1 = tv.get_last_x_days_available_in_high_low_archive(archive_location=test_loc, last_x_days="all")
    t2 = tv.get_last_x_days_available_in_high_low_archive(archive_location=test_loc, last_x_days=5)
    stop = 1


def test_load_high_low_archive():
    res_dir = get_test_resource_loc()
    high_low_dir = osC.append_to_dir(res_dir, 'high-low-lists')

    tv = TradingView()
    tv.load_high_low_archive(archive_location=high_low_dir, last_x_available=30, last_from_date="20231215")

    all_stocks = tv.screener_get_all_stocks()
    market_breakdown = tv.get_sector_industry_breakdown_of_list(stock_list=all_stocks['data'])
    stop = 1
    # ds = tC.add_days_to_date(tC.get_date_today(return_string=True, str_format="%Y%m%d"), -60, input_format="%Y%m%d", specify_string_format="%Y%m%d")
    # tv.load_high_low_archive(archive_location=high_low_dir, date_start=ds, high_low_both='high', period_include_list=[1])

    unique = tv.get_unique_stock_tickers_in_list()
    lly = tv.get_most_recent_data_for_stock_in_archive("LLY")
    lpg = tv.get_most_recent_data_for_stock_in_archive("LPG")
    stop = 1


def test():
    test_load_high_low_archive()
    # test_get_last_x_days_available_in_high_low_archive()
    # test_get_all_industries_in_list()
    # test_get_stocks_by_index_screener()
    # test_indice_archive()
    # test_base_screener_function()
    # test_get_all_stocks_screener()
    # test_high_low_screener()
    # test_get_all_stocks_in_high_low_archive_for_week()


def main():
    test()


if __name__ == '__main__':
    main()
