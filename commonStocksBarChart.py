import commonStocksYahooApi
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import osCommon as osC
from resources.aceCommon import stringCommon as sC
from resources.aceCommon import timeCommon as tC
from resources.aceCommon import listWorkCommon as lC
from resources.aceCommon import mathCommon as mC
from commonStocksYahooApi import YahooFinance
import commonSelenium as cS
import time
import math
import copy


class BarChartHighLowAnalysis:
    """
    This class is a wrapper for working with bar chart high/low archive. It requires a barchart raw data file or
    an archive with multiple barchart data files to work.

    The following is the logic for how the class will work, and an explanation of the dependencies:
        1. This class requires, at minimum, raw data from barchart. The data needs to be created with one of
           the functions in this module:
                selenium_retrieve_stocks_on_highs_and_lows
                selenium_performance_based_stocks_on_highs_and_lows

            Those files are by default kept here:
            resources/grindSundayStocks/barchart_high-lows

            Example file:
            bc-high-lows_20211221173615.json

        2. It will load the data from parsed versions of the files from #1. If a raw file exists that does not have
           a parsed version, it is this classes job to parse it unless "use_raw_data_only" = True. Parsing it means
           that it will add additional stock information to this raw data from the yahoo finance common stock
           module (commonStocksYahooApi.py), It will save this data for later use in a "parsed" file in the same
           location. If the parsed data is already available to the class, then it will just load the parsed data for
           a file instead of the raw data.

           Example file:
           bc-high-lows_20211221173615_parsed.json

        3. More on the parsing processing:
            - Adding stock information from the API takes a long time, about 10 seconds per stock.
            - For this reason, there is an option to try the recent cache (use_recent_cache=True). The way this is
              done is that if the setting is on, when this class parses with the API, it will store the result for
              each ticker in parses in the recent cache file for the next time it parses. If you want to use
              recent cache instead of calling the API, it will search to see if the ticker exists in the recent cache
              before calling Yahoo API. This is useful if you don't care about the freshness of the data on a
              daily basis (e.g., industry and sector data is still useful since this doesn't change daily, where as
              price data is not).
            - The Yahoo finance wrapper being used builds in the necessary API delays to deal with large lists
            - The Yahoo finance wrapper also uses cache, which means for duplicates of stocks in the list, the
              second call will take less than a second

            For these reasons, if you have a lot of files to parse, it is best to do them all in one run of
            the program, due to the caching feature, which greatly improves the speed and ensures we don't hit
            yahoo finance rate limits.

        4. Since there is already so much overhead in the parsing of raw data files, there is an additional, optional
           function that can be used to add more data to the tickers in recent cache. Use "update_recent_cache" to add
           data from additional api's (e.g. td api). This requires that you use recent cache and does not update
           the raw data and parsed files as described in 2/3. Data will be stored in the recent cache.

           Accessing this cache can be done within the class "gsStockCache.py".
    """

    def __init__(self, archive_file_path=None, archive_directory_path=None, use_raw_data_only=False,
                 quit_on_dupes=False, quit_on_data_errors=False, parse_only=False, use_recent_cache=False,
                 clean_recent_cache=False, logging=False, log_path=None, remove_shell=False, start_date=None,
                 end_date=None, date_format="%Y%m%d", td_api_class=None):
        """
        Provide an archive file or archive path (where there are multiple files) to use the class.
        :param archive_file_path:
        :param archive_directory_path:
        :param quit_on_dupes:
        :param quit_on_data_errors:
        :param use_recent_cache:
        :param clean_recent_cache:          bool(), will check the recent cache for any incomplete sector or industry
                                            data and then try to update it if needed. Note: use_recent_cache must also
                                            be true for this parameter to have impact. Within _set_recent_cache

        :param logging:                     bool(), if True, a logging will be turned on. By default, gchla_log.txt
                                            will be placed in the folder where script is ran, unless log_path is
                                            provided.

        :param log_path:                    str(), path (directory path) to where log file should be written. If left
                                            as None, the default path is used (same as current script location.

        :param remove_shell:                bool(), shell companies are removed from the data before summaries are
                                            added and will be treated as if they don't exist. Note: the raw data
                                            (i.e. the data in files) is untouched.

        :param start_date:                  None or date string. Start date is the first date (inclusive) that you
                                            want loaded by the class. First date = first date in time.
                                            This can significantly improve loading and performance if you don't need
                                            the entire archive.

        :param end_date:                    None or date string. End date is the last day (inclusive) that you want
                                            loaded by the class. Last date = most recent date in time. Use together
                                            with start date to load a specific range.


        :param td_api_class                 None or tda api object. This is so you can pass this function an
                                            already created class with cache.

        """
        self.tda_class = td_api_class
        self.archive = archive_directory_path
        self.archive_file = archive_file_path
        self.settings = {"useRawDataOnly": use_raw_data_only,
                         "quitOnDataError": quit_on_data_errors,
                         "quitOnDupes": quit_on_dupes}
        self.data = list()
        self.yahoo_obj = YahooFinance(add_api_delay=True)
        self.all_sectors = list()
        self.all_industries = list()
        self.dates = list()
        self.date_format = date_format
        if start_date is None:
            self.start_date = None
        else:
            self.start_date = tC.convert_date_format(start_date, date_format, to_format="%Y%m%d")

        if end_date is None:
            self.end_date = None
        else:
            self.end_date = tC.convert_date_format(end_date, date_format, to_format="%Y%m%d")

        self.use_recent_cache = use_recent_cache
        self.recent_cache = []
        self.recent_cache_path = None
        self.recent_cache_available = False
        self._set_recent_cache(clean_recent_cache=clean_recent_cache)

        self.remove_shell = remove_shell

        self.log = logging
        self.log_path = log_path
        if self.log:
            self._set_up_log()

        if archive_file_path is None and archive_directory_path is None:
            # skip loading, most features will not work
            print("WARNING: you did not provide a barchart file path or directory path, so this class has no "
                  "data to work with. Limited features will work without data!\n")
        else:
            if use_raw_data_only:
                self._load_raw_data_only()
            else:
                self._check_parse_files()
                self._load_parsed_data()

            self._check_for_duplicate_dates()
            self._check_for_data_errors()
            if remove_shell:
                self._remove_shell_companies_from_data()

            if use_raw_data_only:
                pass
            elif parse_only:
                pass
            else:
                self._clean_data()
                self._create_sector_and_industry_summaries()

    def _clean_data(self):
        """
        Errors found in source data can be fixed here. For example, yahoo sometimes list blank sector name instead
        of 'n/a', which they usually use. Change all of the data to use 'n/a'. Each clean needs to be done on the
        high lists and the low lists.

        :return: None
        """
        data = [x["data"] for x in self.data]

        for d in data:
            frames = [d['1month'], d['3month'], d['6month'], d['12month']]
            for frame in frames:
                counter = 0
                for high in frame['highs']['tickers']:
                    # check if a dict exists, if not, replace it with n/a dict
                    try:
                        test_ticker = high['ticker']
                    except KeyError:
                        frame['highs']['tickers'][counter] = _get_dummy_ticker_dict(frame['highs']['tickers'][counter])

                    # check if sector is blank, if it is, replace it with n/a
                    try:
                        test_sector = high['sector']
                        if test_sector == "":
                            high['sector'] = 'n/a'
                    except KeyError:
                        high.update({'sector': 'n/a'})

                    # check if industry is blank, if it is, replace it with n/a
                    try:
                        test_industry = high['industry']
                        if test_industry == "":
                            high['industry'] = 'n/a'
                    except KeyError:
                        high.update({'industry': 'n/a'})

                    counter = counter + 1

                counter = 0
                for low in frame['lows']['tickers']:
                    # check if a dict exists, if not, replace it with n/a dict
                    try:
                        test_ticker = low['ticker']
                    except KeyError:
                        frame['lows']['tickers'][counter] = _get_dummy_ticker_dict(frame['lows']['tickers'][counter])

                    # check if sector is blank, if it is, replace it with n/a
                    try:
                        test_sector = low['sector']
                        if test_sector == "":
                            low['sector'] = 'n/a'
                    except KeyError:
                        low.update({'sector': 'n/a'})

                    # check if industry is blank, if it is, replace it with n/a
                    try:
                        test_industry = low['industry']
                        if test_industry == "":
                            low['industry'] = 'n/a'
                    except KeyError:
                        low.update({'industry': 'n/a'})

                    counter = counter + 1

    def _set_up_log(self):
        if self.log_path is None:
            cur_path = osC.get_working_dir()
            self.log_path = osC.append_to_dir(cur_path, "gchla_log.txt")
        else:
            self.log_path = osC.append_to_dir(self.log_path, "gchla_log.txt")

    def _create_sector_and_industry_summaries(self):
        """
        This function adds a sector and industry summary to each high/low time frame. It also initializes the
        class variables self.industries and self.sectors, which contain a unique list of all the industries/sectors
        within the working data.

        :return: None
        """
        data = [x["data"] for x in self.data]
        s_list = list()
        i_list = list()
        for d in data:
            frames = [d['1month'], d['3month'], d['6month'], d['12month']]
            for frame in frames:
                high_sectors = [_get_sector(x) for x in frame['highs']['tickers']]
                high_industries = [_get_industry(x) for x in frame['highs']['tickers']]
                low_sectors = [_get_sector(x) for x in frame['lows']['tickers']]
                low_industries = [_get_industry(x) for x in frame['lows']['tickers']]

                unique_sectors_highs = lC.return_unique_values(high_sectors)
                unique_industries_highs = lC.return_unique_values(high_industries)
                unique_sectors_lows = lC.return_unique_values(low_sectors)
                unique_industries_lows = lC.return_unique_values(low_industries)

                high_sectors_dict = dict()
                high_industries_dict = dict()
                low_sectors_dict = dict()
                low_industries_dict = dict()

                for s in unique_sectors_highs:
                    high_sectors_dict.update({s: high_sectors.count(s)})

                for s in unique_sectors_lows:
                    low_sectors_dict.update({s: low_sectors.count(s)})

                for i in unique_industries_highs:
                    high_industries_dict.update({i: high_industries.count(i)})

                for i in unique_industries_lows:
                    low_industries_dict.update({i: low_industries.count(i)})

                frame['highs']['sectorSummary'] = high_sectors_dict.copy()
                frame['highs']['industrySummary'] = high_industries_dict.copy()
                frame['lows']['sectorSummary'] = low_sectors_dict.copy()
                frame['lows']['industrySummary'] = low_industries_dict.copy()

                s_list.extend([_get_sector(x) for x in frame['highs']['tickers']])
                s_list.extend([_get_sector(x) for x in frame['lows']['tickers']])
                i_list.extend([_get_industry(x) for x in frame['highs']['tickers']])
                i_list.extend([_get_industry(x) for x in frame['lows']['tickers']])

        self.all_sectors = lC.return_unique_values(s_list)
        self.all_industries = lC.return_unique_values(i_list)

    def _check_for_duplicate_dates(self):
        self.dates = [x["date"] for x in self.data]
        if lC.check_if_list_has_duplicates(self.dates):
            if self.settings["quitOnDupes"]:
                quit()
            else:
                print("Warning: your archive has days where barchart data was collected more than "
                      "once (duplicate data)")

    def _set_recent_cache(self, clean_recent_cache=False):
        c_fn = "recent_cache.json"
        if self.archive is not None and self.use_recent_cache:
            parent_dir = osC.get_parent_dir_given_full_dir(self.archive)
            dir_check = osC.append_to_dir(parent_dir, "barchart_recent_cache")
            if osC.check_if_dir_exists(dir_check, full_path=1) == 0:
                osC.create_dir(dir_check)
            self.recent_cache_path = osC.append_to_dir(parent_dir, ["barchart_recent_cache", c_fn], list=1)

            if osC.check_if_file_exists(self.recent_cache_path, full_path=1) == 1:
                self.recent_cache_available = True
                if clean_recent_cache:
                    self.clean_recent_cache(report_status_only=False)

                self.recent_cache = fC.load_json_from_file(self.recent_cache_path)
            else:
                # first try last modified file
                parsed_found = False
                parsed_file = ""
                last_mod = osC.get_most_recently_modified_file_in_directory(self.archive)
                if "parsed" in last_mod:
                    parsed_found = True
                    parsed_file = last_mod
                else:
                    check_files = osC.return_files_in_dir_as_strings(self.archive, full_path=True)
                    i = len(check_files) - 1
                    while i > -1:
                        if "parsed" in check_files[i]:
                            parsed_found = True
                            parsed_file = check_files[i]
                            break
                        i = i - 1

                if parsed_found:
                    print("Warning: 'use_recent_cache' is on but there is no recent cache file. Creating a cache "
                          "from the most recently parsed file")
                    self.recent_cache_available = True
                    parsed_data = fC.load_json_from_file(parsed_file)
                    self.recent_cache.extend(parsed_data["1month"]["highs"]["tickers"])
                    self.recent_cache.extend(parsed_data["1month"]["lows"]["tickers"])
                else:
                    print("Error: 'use_recent_cache' is on but there is no recent cache file and no parsed files "
                          "in the provided directory. No cache to use, continuing without recent cache.")
        else:
            if self.use_recent_cache:
                print("Error: 'use_recent_cache' is on, but there is no archive provided, and no cache file to use."
                      "The program will continue, and if parsing is required, it may take awhile.")

    def _check_for_data_errors(self):
        data = [x["data"] for x in self.data]
        counter = 0
        for d in data:
            error_flag = False
            frames = [d['1month'], d['3month'], d['6month'], d['12month']]
            for frame in frames:
                high_errors = frame['highs']['error']
                low_errors = frame['lows']['error']
                if high_errors:
                    if self.settings["quitOnDataError"]:
                        quit()
                    else:
                        print("Warning: there is an error reported in a barchart "
                              "archive, (highs), file = " + self.data[counter]['file'])
                        error_flag = True

                if low_errors:
                    if self.settings["quitOnDataError"]:
                        quit()
                    else:
                        print("Warning: there is an error reported in a barchart "
                              "archive, (lows), file = " + self.data[counter]['file'])
                        error_flag = True

            self.data[counter].update({"fileErrors": error_flag})
            counter = counter + 1

    def _load_raw_data_only(self):
        """
        Load the raw data dumps created by the selenium functions
        """
        if self.archive_file is None and self.archive is None:
            print("Error: you have to provide a file path or a path to a directory where bar chart "
                  "high/low data is located")
        else:
            if self.archive is not None:
                files = osC.return_files_in_dir_as_strings(self.archive, full_path=True)

                self.data = [
                    {"date": osC.extract_file_name_given_full_path(x).split("_")[1][:8],
                     "data": fC.load_json_from_file(x),
                     "file": osC.extract_file_name_given_full_path(x)}
                    for x in files if 'bc-high-lows' in x if 'parsed' not in x
                ]
            else:
                self.data = [{"date": osC.extract_file_name_given_full_path(self.archive_file).split("_")[1][:8],
                              "data": fC.load_json_from_file(self.archive_file)}]

    def _load_parsed_data(self):
        """
        Load the parsed data dumps previously created by this class
        """
        if self.archive_file is None and self.archive is None:
            print("Error: you have to provide a file path or a path to a directory where bar chart "
                  "high/low data is located")
            quit()
        else:
            if self.archive is not None:
                files = osC.return_files_in_dir_as_strings(self.archive, full_path=True)

                if self.end_date is None:
                    temp_end = "40001231"
                else:
                    temp_end = self.end_date

                if self.start_date is None:
                    temp_start = "20200101"
                else:
                    temp_start = self.start_date

                self.data = [
                    {"date": osC.extract_file_name_given_full_path(x).split("_")[1][:8],
                     "data": fC.load_json_from_file(x),
                     "file": osC.extract_file_name_given_full_path(x)}
                    for x in files if 'parsed' in x and
                                      tC.check_if_date_time_string_is_in_given_range(
                                          osC.extract_file_name_given_full_path(x).split("_")[1][:8],
                                          temp_start, temp_end, input_format="%Y%m%d")

                ]
            else:
                self.data = [{"date": osC.extract_file_name_given_full_path(self.archive_file).split("_")[1][:8],
                              "data": fC.load_json_from_file(self.archive_file)}]

            # cascade dates down to data
            for x in self.data:
                date = x['date']
                x['data'].update({"date": date})

    def _check_for_parsed_data(self):
        """
        Each raw data file must have an associated parsed file for all functions to work properly. This function
        will return a list of files that need to be parsed (list will be empty if no files need to be parsed).

        :return: list(), files to parse
        """

        files_to_parse = []
        if self.archive_file is None and self.archive is None:
            print("Error: you have to provide a file path or a path to a directory where bar chart "
                  "high/low data is located")
        else:
            if self.archive is not None:
                files = osC.return_files_in_dir_as_strings(self.archive, full_path=True)
                file_names = [osC.extract_file_name_given_full_path(x) for x in files]

                for fn in file_names:
                    if "parsed" in fn:
                        pass
                    else:
                        ts = fn.split("_")[1].replace(".json", "")
                        check_file = osC.append_to_dir(self.archive, "bc-high-lows_" + ts + "_parsed.json")
                        if osC.check_if_file_exists(check_file, full_path=1) == 1:
                            pass
                        else:
                            files_to_parse.append(osC.append_to_dir(self.archive, fn))
            else:
                test = 1
                # Check make sure the file is parsed, since raw data only is not on
                if "parsed" in self.archive_file:
                    return []
                else:
                    files_to_parse.append(self.archive_file)

        return files_to_parse

    def _check_parse_files(self):
        """
        This function adds information to the raw barchart files and creates a brother file with the data (i.e. parsed)
        :return:
        """

        files_to_parse = self._check_for_parsed_data()
        new_cache_list = list()
        e_fn = osC.create_file_path_string(["errorLog.json"])

        if len(files_to_parse) > 0:
            print("Files need to be updated. This may take awhile...Console updates every 25 stocks")

            for file in files_to_parse:
                temp_json = fC.load_json_from_file(file)

                type_keys = ["highs", "lows"]

                for type_key in type_keys:
                    for time_key in temp_json:
                        new_high_list = list()
                        new_low_list = list()
                        counter = 0
                        print(str(len(temp_json[time_key][type_key]['tickers'])) + " " + type_key
                              + " to collect in " + time_key)
                        start = time.time()
                        for stock in temp_json[time_key][type_key]['tickers']:
                            if counter % 25 == 0:
                                end = time.time()
                                print(str(counter) + " tickers updated, total time taken since last: " +
                                      str(end - start))
                                start = time.time()

                            # first try cache if option says to try it and file is available
                            stock_found = False
                            tick_result = {}
                            if self.use_recent_cache and self.recent_cache_available:
                                tick_result, stock_found = self._try_recent_cache(stock)

                            if stock_found:
                                pass
                            else:
                                tick_result, stock_found = self._retrieve_from_yahoo(stock)
                                if self.use_recent_cache and stock_found:
                                    if tick_result['sector'] == "":
                                        tick_result['sector'] = "n/a"
                                    if tick_result['industry'] == "":
                                        tick_result['industry'] = "n/a"

                                    new_cache_list.append(tick_result)

                            if stock_found and tick_result != {}:
                                if type_key == "highs":
                                    new_high_list.append(tick_result)
                                else:
                                    new_low_list.append(tick_result)

                            else:
                                print("Error: there was a problem retrieving a stock from yahoo or cache. Creating log "
                                      "and exiting program")
                                error_log = {
                                    "error": True,
                                    "parsingFile": file,
                                    "typeKey": type_key,
                                    "count": counter,
                                    "stockWhereErrorOccurred": stock
                                }
                                fC.dump_json_to_file(e_fn, error_log)
                                if self.use_recent_cache:
                                    self.recent_cache.extend(new_cache_list)
                                    fC.dump_json_to_file(self.recent_cache_path, self.recent_cache)
                                quit()

                            counter = counter + 1

                        if type_key == "highs":
                            temp_json[time_key]['highs']['tickers'] = new_high_list.copy()
                        else:
                            temp_json[time_key]['lows']['tickers'] = new_low_list.copy()

                parsed_file = file.replace(".json", "_parsed.json")
                fC.dump_json_to_file(parsed_file, temp_json)
                error_log = {
                    "error": False
                }
                fC.dump_json_to_file(e_fn, error_log)
                if self.use_recent_cache:
                    self.recent_cache.extend(new_cache_list)
                    fC.dump_json_to_file(self.recent_cache_path, self.recent_cache)

    def _try_recent_cache(self, stock_to_try):
        """
        internal sub function to try cache. It updates tick_result and stock_found flag
        :return: tuple(), ticker, flag_update
        """
        temp_res = {}
        i = 0
        flag_update = False
        while i < len(self.recent_cache):
            if stock_to_try == self.recent_cache[i]["ticker"]:
                temp_res = self.recent_cache[i]
                flag_update = True
                break
            i = i + 1

        return temp_res, flag_update

    def _retrieve_from_yahoo(self, stock_to_retrieve):
        """
        :param stock_to_retrieve:
        :return:
        """
        # get data from yahoo, try 10 times as needed
        i = 0
        update_flag = False
        temp_result = {}
        while i < 10:
            try:
                temp_result = self.yahoo_obj.ticker_get_summary(stock_to_retrieve, try_live_cache=True)
                update_flag = True
                break
            except:
                tC.sleep(30)
                print("error with yahoo API, trying again")

            i = i + 1

        return temp_result, update_flag

    def _remove_shell_companies_from_data(self):
        total_removed = 0
        for day_data in self.data:
            frames = ["1month", "3month", "6month", "12month"]
            types = ["highs", "lows"]

            for f in frames:
                for t in types:
                    i = 0
                    while i < len(day_data["data"][f][t]["tickers"]):
                        if day_data["data"][f][t]["tickers"][i]['industry'] == "Shell Companies":
                            day_data["data"][f][t]["tickers"].pop(i)
                            total_removed = total_removed + 1
                            day_data["data"][f][t]["total"] = day_data["data"][f][t]["total"] - 1
                        else:
                            i = i + 1
        # print("Total Shell Companies removed from data: " + str(total_removed))

    def _get_time_frames_for_updating(self):
        data = [x["data"] for x in self.data]
        for d in data:
            return [d['1month'], d['3month'], d['6month'], d['12month']]

    def _get_all_period_dicts_for_data_record(self, data_record, high_or_low):
        """
        This function returns the data dictionaries associated with all periods (1m, 3m, 6m, 12m) for highs or lows as
        specified

        :param data: dict(), a data file dictionary within the object. e.g. self.data[0]['data']
        :return: list(), list of dicts for the specified input
        """

        if high_or_low == "high":
            type_key = 'highs'
        else:
            type_key = 'lows'

        op_list = list()
        periods = ["1month", "3month", "6month", "12month"]
        for period in periods:
            op_list.append(data_record['data'][period][type_key].copy())

        return op_list

    def _create_working_data_given_dates_period_high_low_inputs(self, all_dates, start_date, end_date, stock_frame,
                                                                high_or_low, date_format, sectors, industries):

        # First extract just the dates that are needed
        if all_dates is True:
            temp_data = [x["data"] for x in self.data]  # All dates applicable
        elif type(all_dates) is list:
            temp_data = [x["data"] for x in self.data if tC.convert_date_format(x["date"], date_format=date_format,
                                                                                to_format="%Y%m%d") in all_dates]
        elif start_date == end_date:
            date_key = tC.convert_date_format(start_date, date_format=date_format, to_format="%Y%m%d")
            temp_data = [x["data"] for x in self.data if x["date"] == date_key]
        else:
            start_date = tC.convert_date_format(start_date, date_format=date_format, to_format="%Y%m%d")
            end_date = tC.convert_date_format(end_date, date_format=date_format, to_format="%Y%m%d")
            temp_data = [x["data"] for x in self.data if tC.check_if_date_time_string_is_in_given_range(
                x["date"], start_date, end_date, input_format=date_format)]

        # Now create a copy of just the data that is needed to remove items
        working_data = copy.deepcopy(temp_data)

        # Determine applicable stock frames
        if stock_frame == "all":
            periods = ["1month", "3month", "6month", "12month"]
        elif stock_frame == 1 or stock_frame == "1m":
            periods = ["1month"]
        elif stock_frame == 3 or stock_frame == "3m":
            periods = ["3month"]
        elif stock_frame == 6 or stock_frame == "6m":
            periods = ["6month"]
        elif stock_frame == 12 or stock_frame == "1m":
            periods = ["12month"]
        elif type(stock_frame) is list:
            periods = [str(x) + "month" for x in stock_frame]
        else:
            print("Error: Invalid periods parameter. Utilizing all time periods [1, 3, 6, 12].")
            periods = ["1month", "3month", "6month", "12month"]

        # Get applicable frames
        all_available = ["1month", "3month", "6month", "12month"]
        delete_stock_frames = []
        for item in all_available:
            if item in periods:
                pass  # Keep it in working data
            else:
                delete_stock_frames.append(item)

        for data in working_data:
            for d in delete_stock_frames:
                try:
                    del data[d]
                except:
                    test = 1

        # Remove highs or lows
        if high_or_low.lower() == "both":
            pass
        else:
            if "high" in high_or_low:
                # remove lows
                for data in working_data:
                    for frame in periods:
                        del data[frame]['lows']
            elif "low" in high_or_low:
                # remove highs
                for data in working_data:
                    for frame in periods:
                        del data[frame]['highs']
            else:
                print("Warning: Invalid input for high_or_low. Keeping both highs and lows in analysis.")

        # Remove sectors and industries
        if sectors == "all" and industries == "all":
            pass
        else:
            s_cache = commonStocksYahooApi.get_proper_case_for_industry_or_sector("", get_cache_only=True)
            if sectors == "all":
                pass
            elif sectors != "all" and type(sectors) is list:
                temp_list = list()
                for x in sectors:
                    temp_item = commonStocksYahooApi.get_proper_case_for_industry_or_sector(x,
                                                                                            provide_cache=s_cache).lower()
                    if temp_item == "no match":
                        print("Warning: " + x + " is not a valid sector according to "
                                                "resources\commonStocks\stockClassification\yahooSectorfToIndustry.csv "
                                                ". This file may need updating.")
                        temp_item = x.lower()

                    temp_list.append(temp_item)

                sectors = temp_list

                # first remove sectors as they are highest level
                for data in working_data:
                    for frame_key in data:
                        if frame_key == "date":
                            pass
                        else:
                            for hl_type in data[frame_key]:
                                list_to_filter = data[frame_key][hl_type]["tickers"]
                                new_list = []
                                for tick in list_to_filter:
                                    if tick['sector'].lower() in sectors:
                                        new_list.append(tick)

                                data[frame_key][hl_type]["tickers"] = new_list.copy()
            elif sectors != "all" and type(sectors) == str:
                temp_item = commonStocksYahooApi.get_proper_case_for_industry_or_sector(sectors,
                                                                                        provide_cache=s_cache).lower()
                if temp_item == "no match":
                    print("Warning: " + sectors + " is not a valid sector according to "
                                                  "resources\commonStocks\stockClassification\yahooSectorfToIndustry.csv "
                                                  ". This file may need updating.")
                    temp_item = sectors.lower()

                sectors = [temp_item]

                # first remove sectors as they are highest level
                for data in working_data:
                    for frame_key in data:
                        if frame_key == "date":
                            pass
                        else:
                            for hl_type in data[frame_key]:
                                list_to_filter = data[frame_key][hl_type]["tickers"]
                                new_list = []
                                for tick in list_to_filter:
                                    if tick['sector'].lower() in sectors:
                                        new_list.append(tick)

                                data[frame_key][hl_type]["tickers"] = new_list.copy()
            else:
                print("Error: invalid sectors argument. Sectors must be a list, str, or 'all'. "
                      "Continuing with all sectors.")

            if industries == "all":
                pass
            elif industries != "all" and type(industries) is list:
                temp_list = list()
                for x in industries:
                    temp_item = commonStocksYahooApi.get_proper_case_for_industry_or_sector(
                        x, provide_cache=s_cache).lower()

                    if temp_item == "no match":
                        print("Warning: " + x + " is not a valid industry according to "
                                                "resources\commonStocks\stockClassification\yahooSectorfToIndustry.csv "
                                                ". This file may need updating.")
                        temp_item = x.lower()

                    temp_list.append(temp_item)

                industries = temp_list

                for data in working_data:
                    for frame_key in data:
                        if frame_key == "date":
                            pass
                        else:
                            for hl_type in data[frame_key]:
                                list_to_filter = data[frame_key][hl_type]["tickers"]
                                new_list = []
                                for tick in list_to_filter:
                                    if tick['industry'].lower() in industries:
                                        new_list.append(tick)

                                data[frame_key][hl_type]["tickers"] = new_list.copy()

            elif industries != "all" and type(industries) == str:
                temp_item = commonStocksYahooApi.get_proper_case_for_industry_or_sector(industries,
                                                                                        provide_cache=s_cache).lower()
                if temp_item == "no match":
                    print("Warning: " + industries + " is not a valid industry according to "
                                                     "resources\commonStocks\stockClassification\yahooSectorfToIndustry"
                                                     ".csv "
                                                     ". This file may need updating.")
                    temp_item = industries.lower()

                industries = [temp_item]

                for data in working_data:
                    for frame_key in data:
                        if frame_key == "date":
                            pass
                        else:
                            for hl_type in data[frame_key]:
                                list_to_filter = data[frame_key][hl_type]["tickers"]
                                new_list = []
                                for tick in list_to_filter:
                                    if tick['industry'].lower() in industries:
                                        new_list.append(tick)

                                data[frame_key][hl_type]["tickers"] = new_list.copy()

            else:
                print("Error: invalid industries argument. Industries must be a list, str, or 'all'. "
                      "Continuing with all industries.")

        return working_data

    def _parse_date_input(self, start_date, end_date, date_str_format):
        if start_date is None:
            start_date = "19000101"
        else:
            start_date = tC.convert_date_format(start_date, date_str_format, self.date_format)
        if end_date is None:
            end_date = "40000101"
        else:
            end_date = tC.convert_date_format(end_date, date_str_format, self.date_format)

        return start_date, end_date

    def _parse_stock_frame(self, stock_frame):

        def _convert_to_standard(i):
            if type(i) == int:
                if i == 1:
                    return "1month"
                elif i == 3:
                    return "3month"
                elif i == 6:
                    return "6month"
                elif i == 12:
                    return "12month"
                else:
                    return ["1month", "3month", "6month", "12month"]
            elif type(i) == str:
                if i == '1m':
                    return "1month"
                elif i == '3m':
                    return "3month"
                elif i == "6m":
                    return "6month"
                elif i == "12m":
                    return "12month"
                else:
                    return i

        if stock_frame == "all":
            return ["1month", "3month", "6month", "12month"]
        elif type(stock_frame) == list:
            return [_convert_to_standard(x) for x in stock_frame]
        else:
            return _convert_to_standard(stock_frame)

    def _parse_high_low(self, high_or_low):
        if high_or_low == "both":
            return ["highs", "lows"]
        elif high_or_low.lower() == "high":
            return ["highs"]
        elif high_or_low.lower() == "low":
            return ["lows"]
        else:
            return ["highs", "lows"]

    def _parse_industries(self, industries):
        def _parse_item(i):
            temp_item = commonStocksYahooApi.get_proper_case_for_industry_or_sector(i, provide_cache=s_cache)
            if temp_item == "no match":
                print("Warning: industry input (" + i + ")" + " is not supported in yahoo cache. Using "
                                                              "input as provided")
                temp_item = i

            return temp_item

        if type(industries) == list:
            s_cache = commonStocksYahooApi.get_proper_case_for_industry_or_sector("", get_cache_only=True)
            return [_parse_item(x) for x in industries]
        elif industries == "all":
            return self.all_industries
        else:
            s_cache = commonStocksYahooApi.get_proper_case_for_industry_or_sector("", get_cache_only=True)
            return [_parse_item(industries)]

    def _parse_sectors(self, sectors):
        def _parse_item(i):
            temp_item = commonStocksYahooApi.get_proper_case_for_industry_or_sector(i, provide_cache=s_cache)
            if temp_item == "no match":
                print("Warning: sector input (" + i + ")" + " is not supported in yahoo cache. Using "
                                                            "input as provided")
                temp_item = i

            return temp_item

        if type(sectors) == list:
            s_cache = commonStocksYahooApi.get_proper_case_for_industry_or_sector("", get_cache_only=True)
            return [_parse_item(x) for x in sectors]
        elif sectors == "all":
            return self.all_sectors
        else:
            s_cache = commonStocksYahooApi.get_proper_case_for_industry_or_sector("", get_cache_only=True)
            return [_parse_item(sectors)]

    def get_unique_ticker_lists_from_data(self, provided_data=None):
        if provided_data is None:
            working_data = self._create_working_data_given_dates_period_high_low_inputs(True, "", "", "all", "both",
                                                                                        self.date_format, "all", "all")
        else:
            working_data = provided_data

        just_tickers = list()
        ticker_data = list()
        for data in working_data:
            for frame_key in data:
                if frame_key == "date":
                    pass
                else:
                    for hl_type in data[frame_key]:
                        list_to_filter = data[frame_key][hl_type]["tickers"]
                        for tick in list_to_filter:
                            if tick['ticker'] in just_tickers:
                                pass
                            else:
                                just_tickers.append(tick['ticker'])
                                ticker_data.append(tick)

        return {
            "tickersOnly": just_tickers,
            "tickerData": ticker_data
        }

    def get_sector_summary_chart_data(self, sectors="all", stock_frame="all", all_dates=True, start_date=None,
                                      end_date=None, date_str_format="%Y%m%d"):
        working_data = self._create_working_data_given_dates_period_high_low_inputs(all_dates, start_date, end_date,
                                                                                    stock_frame, "both",
                                                                                    date_str_format, sectors,
                                                                                    "all")

        s_cache = commonStocksYahooApi.get_proper_case_for_industry_or_sector("", get_cache_only=True)

        # Create the output dict skeleton based on settings
        sector_dict = dict()
        if sectors == "all":
            for s in self.all_sectors:
                sector_dict.update(
                    {s: {"1monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                         "3monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                         "6monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                         "12monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []}
                         }})
            report_sectors = self.all_sectors.copy()
        elif type(sectors) is list:
            for s in sectors:
                sc = commonStocksYahooApi.get_proper_case_for_industry_or_sector(s, provide_cache=s_cache)
                sector_dict.update(
                    {sc: {"1monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                          "3monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                          "6monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                          "12monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []}
                          }})
            report_sectors = sectors
        else:
            print("Error: invalid sectors argument. Sectors must be a list or 'all'. Continuing with all sectors")
            report_sectors = self.all_sectors.copy()

        for data in working_data:
            date = data["date"]
            for frame_key in data:
                if frame_key == "date":
                    pass
                else:
                    # Get applicable sector summaries and add sectors to report
                    hsum = data[frame_key]['highs']['sectorSummary']
                    lsum = data[frame_key]['lows']['sectorSummary']
                    for s in report_sectors:
                        sp = commonStocksYahooApi.get_proper_case_for_industry_or_sector(s, provide_cache=s_cache)
                        high_count = _get_sector_or_industry_count_from_summary(hsum, sp)
                        low_count = _get_sector_or_industry_count_from_summary(lsum, sp)

                        if low_count == 0 and high_count > 0:
                            hl_ratio = float("inf")
                        elif low_count == 0 and high_count == 0:
                            hl_ratio = 0
                        else:
                            hl_ratio = mC.pretty_round_function(high_count / low_count)

                        sector_dict[sp][frame_key + "Summary"]['highs'].append(high_count)
                        sector_dict[sp][frame_key + "Summary"]['lows'].append(low_count)
                        sector_dict[sp][frame_key + "Summary"]['hlRatios'].append(hl_ratio)
                        sector_dict[sp][frame_key + "Summary"]['hlPlusMinus'].append(high_count - low_count)
                        sector_dict[sp][frame_key + "Summary"]['dates'].append(date)

        return sector_dict

    def get_industry_summary_chart_data(self, industries="all", stock_frame="all", all_dates=True, start_date=None,
                                        end_date=None, date_str_format="%Y%m%d"):
        working_data = self._create_working_data_given_dates_period_high_low_inputs(all_dates, start_date, end_date,
                                                                                    stock_frame, "both",
                                                                                    date_str_format, "all",
                                                                                    industries)

        i_cache = commonStocksYahooApi.get_proper_case_for_industry_or_sector("", get_cache_only=True)

        # Create the output dict skeleton based on settings
        industry_dict = dict()
        if industries == "all":
            for i in self.all_industries:
                industry_dict.update(
                    {i: {"1monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                         "3monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                         "6monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                         "12monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []}
                         }})
            report_industries = self.all_industries.copy()
        elif type(industries) is list:
            for i in industries:
                ic = commonStocksYahooApi.get_proper_case_for_industry_or_sector(i, provide_cache=i_cache)
                industry_dict.update(
                    {ic: {"1monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                          "3monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                          "6monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []},
                          "12monthSummary": {"dates": [], "highs": [], "lows": [], "hlRatios": [], "hlPlusMinus": []}
                          }})
            report_industries = industries
        else:
            print("Error: invalid sectors argument. Sectors must be a list or 'all'. Continuing with all sectors")
            report_industries = self.all_industries.copy()

        for data in working_data:
            date = data["date"]
            for frame_key in data:
                if frame_key == "date":
                    pass
                else:
                    # Get applicable sector summaries and add sectors to report
                    hsum = data[frame_key]['highs']['industrySummary']
                    lsum = data[frame_key]['lows']['industrySummary']
                    for i in report_industries:
                        ip = commonStocksYahooApi.get_proper_case_for_industry_or_sector(i, provide_cache=i_cache)
                        if ip == 'no match':
                            ip = i
                        high_count = _get_sector_or_industry_count_from_summary(hsum, ip)
                        low_count = _get_sector_or_industry_count_from_summary(lsum, ip)

                        if low_count == 0 and high_count > 0:
                            hl_ratio = float("inf")
                        elif low_count == 0 and high_count == 0:
                            hl_ratio = 0
                        else:
                            hl_ratio = mC.pretty_round_function(high_count / low_count)

                        industry_dict[ip][frame_key + "Summary"]['highs'].append(high_count)
                        industry_dict[ip][frame_key + "Summary"]['lows'].append(low_count)
                        industry_dict[ip][frame_key + "Summary"]['hlRatios'].append(hl_ratio)
                        industry_dict[ip][frame_key + "Summary"]['hlPlusMinus'].append(high_count - low_count)
                        industry_dict[ip][frame_key + "Summary"]['dates'].append(date)

        return industry_dict

    def get_stock_list_given_parameters(self, industries="all", sectors="all", stock_frame="all", high_or_low="both",
                                        all_dates=True, start_date=None, end_date=None, date_str_format="%Y%m%d"):
        """

        :param industries:
        :param sectors:
        :param stock_frame:         str(), 1month, 3month, 6month, 12month
        :param high_or_low:
        :param all_dates:
        :param start_date:
        :param end_date:
        :param date_str_format:
        :return:
        """

        working_data = self._create_working_data_given_dates_period_high_low_inputs(all_dates, start_date, end_date,
                                                                                    stock_frame, high_or_low,
                                                                                    date_str_format, sectors,
                                                                                    industries)
        return self.get_unique_ticker_lists_from_data(provided_data=working_data)

    def get_dates_in_data_as_list(self):
        return self.dates

    def get_ticker_data_from_recent_cache(self, ticker):
        """
        This function requires that recent cache is being used. It returns the data available in recent cache for the
        ticker provided. If no ticker is found, False is returned.

        :param ticker:  str(), ticker
        :return:        dict(), or False if not found.
        """

        if self.recent_cache_available:
            for tick in self.recent_cache:
                if tick["ticker"].lower() == ticker.lower():
                    return tick
            return False
        else:
            return "No recent cache available. This function requires that use_recent_cache=True"

    def report_on_parsed_data(self, report_sector_industry=True, console_print=True):
        """
        This function looks at the parsed data available in the object to see it's completeness based on parameters
        given
        :param report_sector_industry:  bool(), True report will include looking into the complete-ness of this data
        :param console_print: bool(), If true, will print the list to the console.
        :return: list(), list of dicts constituting a report.
        """

        op_list = list()
        if report_sector_industry:
            total_sectors_missing = 0
            total_industries_missing = 0
            for record in self.data:
                temp_file = record['file']
                temp_highs = self._get_all_period_dicts_for_data_record(record, "high")
                temp_lows = self._get_all_period_dicts_for_data_record(record, "low")
                try:
                    total_na_highs_sector = temp_highs[0]['sectorSummary']["n/a"]
                except KeyError:
                    total_na_highs_sector = 0
                try:
                    total_na_lows_sector = temp_lows[0]['sectorSummary']["n/a"]
                except KeyError:
                    total_na_lows_sector = 0
                try:
                    total_na_highs_industry = temp_highs[0]['industrySummary']['n/a']
                except KeyError:
                    total_na_highs_industry = 0
                try:
                    total_na_lows_industry = temp_lows[0]['industrySummary']['n/a']
                except KeyError:
                    total_na_lows_industry = 0

                total_industries_missing = total_industries_missing + total_na_lows_industry + total_na_highs_industry
                total_sectors_missing = total_sectors_missing + total_na_highs_sector + total_na_lows_sector

                op_list.append(
                    {"file": temp_file,
                     "totalIndustriesMissing": total_na_lows_industry + total_na_highs_industry,
                     "totalSectorsMissing": total_na_lows_sector + total_na_highs_sector}
                )

            op_list.append({
                "totalSectorsMissing": total_sectors_missing,
                "totalIndustriesMissing": total_industries_missing
            })

        if console_print:
            for item in op_list:
                print(item)

        return op_list

    def update_parsed_files_na(self, use_recent_cache=True, use_recent_cache_only=False):
        """
        This function goes through each parsed file and tries to replace any stocks with n/a data.
        :param use_recent_cache:
        :param use_recent_cache_only:
        :return:
        """

        # first report on the status
        report = self.report_on_parsed_data(console_print=False)
        print(report[len(report) - 1])

        total_fixed = 0
        for record in self.data:
            fixed_current_record = 0
            temp_file = osC.append_to_dir(self.archive, record['file'])
            one_low = record['data']['1month']['lows']['tickers']
            one_high = record['data']['1month']['highs']['tickers']

            one_low_na_list = [x for x in one_low if x['sector'] == "n/a" or x['industry'] == 'n/a']
            one_high_na_list = [x for x in one_high if x['sector'] == "n/a" or x['industry'] == 'n/a']

            stocks_to_fix_highs = list()
            for tick_data in one_high_na_list:
                if use_recent_cache and use_recent_cache_only:
                    res, stock_found = self._try_recent_cache(tick_data['ticker'])
                else:
                    if use_recent_cache:
                        res, stock_found = self._try_recent_cache(tick_data['ticker'])
                        if stock_found:
                            if res['sector'] == 'n/a' or res['industry'] == 'n/a':
                                pass
                            else:
                                stocks_to_fix_highs.append(res)

            stocks_to_fix_lows = list()
            for tick_data in one_low_na_list:
                if use_recent_cache and use_recent_cache_only:
                    res, stock_found = self._try_recent_cache(tick_data['ticker'])
                else:
                    stock_found = False
                    if use_recent_cache:
                        res, stock_found = self._try_recent_cache(tick_data['ticker'])
                        if stock_found:
                            if res['sector'] == 'n/a' or res['industry'] == 'n/a':
                                pass
                            else:
                                stocks_to_fix_lows.append(res)

                    if stock_found:
                        pass
                    else:
                        print("trying yahoo for stock " + tick_data['ticker'])
                        res, stock_found = self._retrieve_from_yahoo(tick_data['ticker'])
                        if self.use_recent_cache and stock_found:
                            if res['sector'] == "" or res['industry'] == "":
                                print("no sector or industry data available")
                                pass
                            else:
                                print("found sector and industry data")
                                stocks_to_fix_lows.append(res)

            periods = ["1month", "3month", "6month", "12month"]
            for period in periods:
                for sf in stocks_to_fix_highs:
                    i = 0
                    while i < len(record['data'][period]['highs']['tickers']):
                        if sf['ticker'] == record['data'][period]['highs']['tickers'][i]['ticker']:
                            record['data'][period]['highs']['tickers'][i] = sf
                            fixed_current_record = fixed_current_record + 1
                            total_fixed = total_fixed + 1
                            break
                        i = i + 1

                for sf in stocks_to_fix_lows:
                    i = 0
                    while i < len(record['data'][period]['lows']['tickers']):
                        if sf['ticker'] == record['data'][period]['lows']['tickers'][i]['ticker']:
                            record['data'][period]['lows']['tickers'][i] = sf
                            total_fixed = total_fixed + 1
                            fixed_current_record = fixed_current_record + 1
                            break
                        i = i + 1

            if fixed_current_record > 0:
                print("Fixed " + str(fixed_current_record) + " in the file: " + temp_file + ". Overwriting the file...")
                temp_json = fC.load_json_from_file(temp_file)
                temp_json["1month"]["highs"]["tickers"] = record["data"]["1month"]["highs"]["tickers"]
                temp_json["3month"]["highs"]["tickers"] = record["data"]["3month"]["highs"]["tickers"]
                temp_json["6month"]["highs"]["tickers"] = record["data"]["6month"]["highs"]["tickers"]
                temp_json["12month"]["highs"]["tickers"] = record["data"]["12month"]["highs"]["tickers"]

                temp_json["1month"]["lows"]["tickers"] = record["data"]["1month"]["lows"]["tickers"]
                temp_json["3month"]["lows"]["tickers"] = record["data"]["3month"]["lows"]["tickers"]
                temp_json["6month"]["lows"]["tickers"] = record["data"]["6month"]["lows"]["tickers"]
                temp_json["12month"]["lows"]["tickers"] = record["data"]["12month"]["lows"]["tickers"]

                fC.dump_json_to_file(temp_file, temp_json)

        stop = 1

    def clean_recent_cache(self, report_status_only=False):
        try:
            temp_cache = fC.load_json_from_file(self.recent_cache_path)
        except:
            print("There was an error trying to load the recent cache. Check it exists for your current working"
                  "archive.")
            return None

        # First report on the status of recent cache
        i = 0
        report_sector_missing = 0
        report_industry_missing = 0
        ticker_list = [x['ticker'] for x in temp_cache]

        while i < len(temp_cache):
            temp_tick = temp_cache[i]
            if temp_tick['sector'] == 'n/a':
                report_sector_missing = report_sector_missing + 1
            if temp_tick['industry'] == 'n/a':
                report_industry_missing = report_industry_missing + 1
            i = i + 1

        print("There are a total of " + str(len(ticker_list)) + " tickers in recent cache...")
        print("There are a total of " + str(report_sector_missing) +
              " tickers without SECTOR data in the recent cache...")
        print("There are a total of " + str(report_industry_missing) +
              " tickers without INDUSTRY data in the recent cache...")

        if report_status_only:
            return None

        stop = 1
        fC.dump_json_to_file(self.recent_cache_path, temp_cache)

        print("\n\nStarting to clean cache")
        clean_cache = list()
        i = 0
        total_clean = 0
        total_missing = 0
        while i < len(temp_cache):
            temp_tick = temp_cache[i]
            if temp_tick['sector'] == 'n/a':
                total_missing = total_missing + 1
                print(temp_tick['ticker'] + " does not have sector info. Trying to replace...")
                tick_result, stock_found = self._retrieve_from_yahoo(temp_tick['ticker'])
                if stock_found:
                    if tick_result['sector'] != "n/a" and tick_result['industry'] != "n/a":
                        print(temp_tick['ticker'] + " was fixed. Replacing the cache with fixed version.")
                        total_clean = total_clean + 1
                        clean_cache.append(tick_result)
                    else:
                        print(temp_tick['ticker'] + " information is still missing. Not replacing.")
                        clean_cache.append(temp_cache[i])
                else:
                    print(temp_tick['ticker'] + " information is still missing. Not replacing.")
                    clean_cache.append(temp_cache[i])
            elif temp_tick['industry'] == 'n/a':
                total_missing = total_missing + 1
                print(temp_tick['ticker'] + " does not have industry info. Trying to replace...")
                tick_result, stock_found = self._retrieve_from_yahoo(temp_tick['ticker'])
                if stock_found:
                    if tick_result['sector'] != "n/a" and tick_result['industry'] != "n/a":
                        print(temp_tick['ticker'] + " was fixed. Replacing the cache with fixed version.")
                        total_clean = total_clean + 1
                        clean_cache.append(tick_result)
                    else:
                        print(temp_tick['ticker'] + " information is still missing. Not replacing.")
                        clean_cache.append(temp_cache[i])
                else:
                    print(temp_tick['ticker'] + " information is still missing. Not replacing.")
                    clean_cache.append(temp_cache[i])
            else:
                clean_cache.append(temp_cache[i])
            i = i + 1

        print("Clean complete:\nTotal Incompletes Found=" + str(total_missing) + "\nTotal Cleaned=" +
              str(total_clean))

        fC.dump_json_to_file(self.recent_cache_path, clean_cache)

    def update_recent_cache(self, report_only=False, no_value_only=False, provide_cache_file_location=None):
        """
        This function will update the recent cache with api's other than yahoo. For example, tda.
        Currently added:
        10 day average volume (sma) = "tdAveVolume10d"
        last_close = "tdLastClose"
        52wk high = "td52WeekHigh"
        52wk low = "td52WeekLow

        :param report_only:                 bool(), if True, does not update, just reports on th status of cache that
                                            has been updated.

        :param no_value_only:               bool(), if True, only items with no value or no field will be tried to be
                                            updated.

        :param provide_cache_file_location: str(), if location is given, the cache file at the provided location will
                                            be updated instead of the location associated with the class.
                                            Note: a cache file is only associated with the class if an archive or
                                            file path is provided when instantiating. So this option must be used if
                                            no file path or archive is provided to the class at initiation.
        :return:
        """

        def _check_td_10d_volume_status():
            """
            :return: dict() of total entries, no_field, null_value, valid_value totals
            """
            no_field = 0
            null_value = 0
            valid_value = 0
            total_entries = len(temp_cache)

            b = 0
            while b < len(temp_cache):
                try:
                    temp_value = temp_cache[b]["tdAveVolume10d"]
                    if temp_value is None:
                        null_value = null_value + 1
                    else:
                        valid_value = valid_value + 1

                except KeyError:
                    no_field = no_field + 1

                b = b + 1

            return {"total": total_entries, "noField": no_field, "noValue": null_value, "validValue": valid_value}

        try:
            if provide_cache_file_location is None:
                temp_cache = fC.load_json_from_file(self.recent_cache_path)
            else:
                temp_cache = fC.load_json_from_file(provide_cache_file_location)
        except:
            print("There was an error trying to load the recent cache. Check it exists for your current working"
                  "archive.")
            return None

        if report_only:
            ten_day_volume_status = _check_td_10d_volume_status()
            print("\n** 10 day Volume Status **")
            print("No Field = " + str(ten_day_volume_status["noField"]) + "/" + str(ten_day_volume_status["total"]))
            print("No Value = " + str(ten_day_volume_status["noValue"]) + "/" + str(ten_day_volume_status["total"]))
            print("Valid = " + str(ten_day_volume_status["validValue"]) + "/" + str(ten_day_volume_status["total"]))

        else:
            if self.tda_class is None:
                import commonStocksTdApi
                td = commonStocksTdApi.Td(add_api_delay=True)
                # using td api as it is much faster for this data
            else:
                td = self.tda_class

            if no_value_only:
                volume_status = _check_td_10d_volume_status()
                print("Trying only items with no field or no values")
                print("No Field = " + str(volume_status["noField"]) + "/" + str(volume_status["total"]))
                print("No Value = " + str(volume_status["noValue"]) + "/" + str(volume_status["total"]) + "\n******")

                i = 0
                while i < len(temp_cache):
                    temp_tick = temp_cache[i]

                    test_value = 0
                    has_field = True
                    try:
                        test_value = temp_tick["tdAveVolume10d"]
                    except KeyError:
                        # No field, so try to get value and add field
                        has_field = False
                        try:
                            td_volume = td.get_volume_averages(temp_tick['ticker'], period="10d")
                            temp_cache[i].update({"tdAveVolume10d": td_volume})
                        except:
                            # Failed again, make volume None
                            temp_cache[i].update({"tdAveVolume10d": None})

                    if has_field:
                        if test_value is None:
                            print("Trying to update: " + temp_tick["ticker"])
                            try:
                                td_volume = td.get_volume_averages(temp_tick['ticker'], period="10d")
                            except:
                                td_volume = None
                                print("TD API failed...")
                                pass

                            if td_volume is None:
                                print("Could not get volume...\n")
                            else:
                                temp_cache[i].update({"tdAveVolume10d": td_volume})
                                print("Added a valid volume...\n")

                    i = i + 1
            else:
                dead_tickers = []
                print("There are a total of " + str(len(temp_cache)) + " tickers in recent cache...")
                print("\n\nStarting the update process")
                i = 0
                while i < len(temp_cache):
                    temp_tick = temp_cache[i]

                    a = 0
                    volume_needed = True
                    quote_needed = True
                    td_volume = None
                    td_last_close = None
                    td_52_high = None
                    td_52_low = None
                    while a < 3:
                        try:
                            td_volume = td.get_volume_averages(temp_tick['ticker'], period="10d")
                            volume_needed = False
                        except:
                            pass

                        try:
                            td_quote = td.get_stock_quote(temp_tick['ticker'])
                            td_last_close = td_quote[temp_tick['ticker']]['closePrice']
                            td_52_high = td_quote[temp_tick['ticker']]['52WkHigh']
                            td_52_low = td_quote[temp_tick['ticker']]['52WkLow']
                            quote_needed = False
                        except:
                            pass

                        if volume_needed or quote_needed:
                            tC.sleep(10)
                            if a == 2:
                                print("Tried 3 times and failed, adding ticker to dead tickers, moving to next ticker")
                                dead_tickers.append(temp_tick['ticker'])
                            else:
                                print("General network or td error, trying again")
                        else:
                            break

                        a = a + 1

                    temp_cache[i].update({"tdAveVolume10d": td_volume})
                    temp_cache[i].update({"tdLastClose": td_last_close})
                    temp_cache[i].update({"td52WeekHigh": td_52_high})
                    temp_cache[i].update({"td52WeekLow": td_52_low})

                    i = i + 1

                    if i % 10 == 0:
                        print(str(i) + "/" + str(len(temp_cache)) + " complete")

            if provide_cache_file_location is None:
                fC.dump_json_to_file(self.recent_cache_path, temp_cache)
            else:
                fC.dump_json_to_file(provide_cache_file_location, temp_cache)
            print("Overwrote the cache file with latest prices... complete")

            return dead_tickers

    def fix_duplicates_in_recent_cache(self):
        """
        There should not be duplicates in recent cache. If there is this function can fix them.
        :return:
        """
        try:
            temp_cache = fC.load_json_from_file(self.recent_cache_path)
        except:
            print("There was an error tryihng to load the recent cache. Check it exists for your current working"
                  "archive.")
            return None

        ticker_list = [x['ticker'] for x in temp_cache]
        unique_tickers = lC.return_unique_values(ticker_list)
        unique_ticker_data = list()
        for ticker in unique_tickers:
            found_data = False
            for tick_data in temp_cache:
                if tick_data['ticker'] == ticker:
                    if tick_data['sector'] == 'n/a':
                        bad_data = tick_data
                        pass
                    else:
                        unique_ticker_data.append(tick_data)
                        found_data = True
                        break

            if found_data:
                pass
            else:
                unique_ticker_data.append(bad_data)

        fC.dump_json_to_file(self.recent_cache_path, unique_ticker_data)

    def no_dc_get_stock_list_given_parameters(self, industries="all", sectors="all", stock_frame="all",
                                              high_or_low="both", start_date=None, end_date=None,
                                              date_str_format="%Y%m%d"):

        start_date, end_date = self._parse_date_input(start_date, end_date, date_str_format)
        stock_frame = self._parse_stock_frame(stock_frame)
        high_low = self._parse_high_low(high_or_low)


        # Get all applicable tickers with event type (high/low), dates, and stock frame parameters
        all_tickers = []
        date_check = tC.check_if_date_time_string_is_in_given_range
        for day in self.data:
            if date_check(day["date"], start_date, end_date, input_format=self.date_format):
                for frame in day['data']:
                    if frame in stock_frame:
                        for event_type in day['data'][frame]:
                            if event_type in high_low:
                                [all_tickers.append(x) for x in day['data'][frame][event_type]['tickers']]


        # sort by industry
        if industries == "all":
            pass
        else:
            industries = self._parse_industries(industries)
            all_tickers = [x for x in all_tickers if x["industry"] in industries]

        if sectors == "all":
            pass
        else:
            sectors = self._parse_sectors(sectors)
            all_tickers = [x for x in all_tickers if x["sector"] in sectors]

        return lC.return_unique_values(all_tickers)


class BarChartDataCollection:
    def __init__(self, headless_collection=True, wait_for_content_time=5):
        self.linux = not osC.is_platform_windows()
        self.headless = headless_collection
        self.wait_time = wait_for_content_time
        self.barchart_url = "https://www.barchart.com/"
        self.driver = None

    def _check_create_selenium_object(self):
        if self.driver is None:
            if self.headless:
                self.driver = cS.create_headless_driver_no_url(linux=self.linux)
            else:
                self.driver = cS.create_driver_no_url()
        else:
            pass

    def _quit_driver(self):
        if self.driver is None:
            pass
        else:
            self.driver.quit()

    def retrieve_stocks_high_lows(self, one_month=True, three_month=True, six_month=True, twelve_month=True,
                                  save_dir=None):

        fn_base = "bc-high-lows_"

        op_dict = {
            "1month": {"highs": {}, "lows": {}},
            "3month": {"highs": {}, "lows": {}},
            "6month": {"highs": {}, "lows": {}},
            "12month": {"highs": {}, "lows": {}}
        }

        start_time = time.time()
        if one_month:
            # Highs
            print("starting 1mo highs...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('1m', 'highs')
            op_dict["1month"]["highs"] = self._selenium_gather_stocks(url_list)

            # Lows
            print("starting 1mo lows...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('1m', 'lows')
            op_dict["1month"]["lows"] = self._selenium_gather_stocks(url_list)
        if three_month:
            # Highs
            print("starting 3mo highs...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('3m', 'highs')
            op_dict["3month"]["highs"] = self._selenium_gather_stocks(url_list)

            # Lows
            print("starting 3mo lows...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('3m', 'lows')
            op_dict["3month"]["lows"] = self._selenium_gather_stocks(url_list)
        if six_month:
            # Highs
            print("starting 6mo highs...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('6m', 'highs')
            op_dict["6month"]["highs"] = self._selenium_gather_stocks(url_list)

            # Lows
            print("starting 6mo lows...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('6m', 'lows')
            op_dict["6month"]["lows"] = self._selenium_gather_stocks(url_list)
        if twelve_month:
            # Highs
            print("starting 12mo highs...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('1y', 'highs')
            op_dict["12month"]["highs"] = self._selenium_gather_stocks(url_list)

            # Lows
            print("starting 12mo lows...total time to this = " + str(time.time() - start_time))
            url_list = self._construct_high_low_urls_for_period('1y', 'lows')
            op_dict["12month"]["lows"] = self._selenium_gather_stocks(url_list)


        self._quit_driver()
        fn = fn_base + tC.create_time_stamp_new() + ".json"
        if save_dir is None:
            print("Collection completing, saving to current directory")
            fC.dump_json_to_file(fn, op_dict)
            fp = fn
        else:
            print("Collection completing, saving to " + save_dir)
            fp = osC.append_to_dir(save_dir, fn)
            fC.dump_json_to_file(fp, op_dict)

        return fp, op_dict




    def _construct_high_low_urls_for_period(self, time_frame, price_type):
        """
        This function creates a list of URLs for the time period provided. Given the nature of the barchart data and
        the load it puts on PC's for gathering the data, this function provides page URLs so that the class can get
        the data one page at a time. This prevents timeouts that occur when trying to load all stocks on the "all"
        page.

        The retrieve stock function will have to protect against a page not being existent.

        For example:
        [url_page1, url_page2, url_page3, url_page4, url_page5, url_page6, etc...]

        The retrieve function will stop once a page does not exist. It is implemented this way so that we don't
        rely on trying to gather page information from the site (as that info may change on the site and break
        the implementation).

        :param time_frame:      str(), 1m, 3m, 6m, 1y
        :param price_type:      str(), highs, lows
        :return:
        """

        base_url = self.barchart_url + "stocks/highs-lows/" + price_type
        time_frame_url = "?timeFrame=" + time_frame
        page_num_url = "&page="

        url_list = []
        i = 1
        while i < 21:
            url_list.append(base_url + time_frame_url + page_num_url + str(i))
            i = i + 1

        return url_list

    def _selenium_gather_stocks(self, url_list):
        self._check_create_selenium_object()

        table_check = '//*[@id="main-content-column"]/div/div[8]'
        total_tickers = []
        counter = 1
        for url in url_list:
            print("Retrieving page " + str(counter) + " of tickers..")
            self.driver.get(url)

            if cS.wait_for_page(self.driver, table_check, 15):
                tC.sleep(self.wait_time)
                if self.driver.current_url != url:
                    # When we put a page url that does not exist, we get redirected to the main
                    print("Page did not load, no more tickers to gather")
                    break
                else:
                    table = cS.find_element_by_xpath(self.driver, table_check)
                    table_entries = table.text.split("\n")
                    tickers = [x for x in table_entries if x.isupper() and ":" not in x]
                    total_tickers.extend(tickers)
                    print("total collected = " + str(len(tickers)))

            counter = counter + 1

        return {
            "error": False,
            "total": len(total_tickers),
            "tickers": total_tickers,
        }




def selenium_retrieve_stocks_on_highs_and_lows(one_month=True, three_month=True, six_month=True, twelve_month=True,
                                               save="no", headless=True, linux=False, wait_time=4):
    op_dict = {
        "1month": {"highs": {}, "lows": {}},
        "3month": {"highs": {}, "lows": {}},
        "6month": {"highs": {}, "lows": {}},
        "12month": {"highs": {}, "lows": {}}
    }

    start_time = time.time()
    if one_month:
        print("starting 1mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(1, "high")
        op_dict["1month"]["highs"] = _selenium_gather_highs_lows(url, headless, linux=linux,
                                                                 wait_for_content_time=wait_time)
        print("starting 1mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(1, "low")
        op_dict["1month"]["lows"] = _selenium_gather_highs_lows(url, headless, linux=linux,
                                                                wait_for_content_time=wait_time)
    if three_month:
        print("starting 3mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(3, "high")
        op_dict["3month"]["highs"] = _selenium_gather_highs_lows(url, headless, linux=linux,
                                                                 wait_for_content_time=wait_time)
        print("starting 3mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(3, "low")
        op_dict["3month"]["lows"] = _selenium_gather_highs_lows(url, headless, linux=linux,
                                                                wait_for_content_time=wait_time)
    if six_month:
        print("starting 6mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(6, "high")
        op_dict["6month"]["highs"] = _selenium_gather_highs_lows(url, headless, linux=linux)
        print("starting 6mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(6, "low")
        op_dict["6month"]["lows"] = _selenium_gather_highs_lows(url, headless, linux=linux)
    if twelve_month:
        print("starting 12mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(12, "high")
        op_dict["12month"]["highs"] = _selenium_gather_highs_lows(url, headless, linux=linux)
        print("starting 12mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(12, "low")
        op_dict["12month"]["lows"] = _selenium_gather_highs_lows(url, headless, linux=linux)

    if save == "no":
        pass
    else:
        fC.dump_json_to_file(save, op_dict)

    return op_dict


def selenium_performance_based_stocks_on_highs_and_lows(one_month=True, three_month=True, six_month=True,
                                                        twelve_month=True, save="no", headless=True, linux=True):
    """
    The output of this function is identical to selenium_retrieve_stocks_on_highs_and_lows

    This function should be used on raspberry pi's or computers with ass processors/memory.
    Instead of loading a page with all tickers, it goes through each page with a limit of 100 tickers per, so that the
    browser doesn't get bogged down with a huge table.

    It is a separate function because the maintenance of this function is separate from the get it done version
    (normal version).

    :param one_month:
    :param three_month:
    :param six_month:
    :param twelve_month:
    :param save:
    :param headless:
    :param linux:
    :return:
    """

    op_dict = {
        "1month": {"highs": {}, "lows": {}},
        "3month": {"highs": {}, "lows": {}},
        "6month": {"highs": {}, "lows": {}},
        "12month": {"highs": {}, "lows": {}}
    }

    start_time = time.time()
    if one_month:
        print("starting 1mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(1, "high")
        op_dict["1month"]["highs"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)
        print("starting 1mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(1, "low")
        op_dict["1month"]["lows"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)
    if three_month:
        print("starting 3mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(3, "high")
        op_dict["3month"]["highs"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)
        print("starting 3mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(3, "low")
        op_dict["3month"]["lows"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)
    if six_month:
        print("starting 6mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(6, "high")
        op_dict["6month"]["highs"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)
        print("starting 6mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(6, "low")
        op_dict["6month"]["lows"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)
    if twelve_month:
        print("starting 12mo highs...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(12, "high")
        op_dict["12month"]["highs"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)
        print("starting 12mo lows...total time to this = " + str(time.time() - start_time))
        url = _construct_url_for_selenium(12, "low")
        op_dict["12month"]["lows"] = _selenium_gather_highs_lows_performance_based(url, headless, linux=linux)

    if save == "no":
        pass
    else:
        fC.dump_json_to_file(save, op_dict)

    return op_dict


def _selenium_gather_highs_lows(url, headless=True, linux=False, wait_for_content_time=4):
    if headless:
        b = cS.create_headless_driver_url(url, linux=linux)
    else:
        b = cS.create_browser_object_sel(url)

    table_check = '//*[@id="main-content-column"]/div/div[7]'
    # show_all_xpath = '//*[@id="main-content-column"]/div/div[7]/div/div[3]/div[2]/a[8]'

    tickers = list()
    if cS.wait_for_page(b, table_check, 15):
        tC.sleep(wait_for_content_time)
        table = cS.find_element_by_xpath(b, '//*[@id="main-content-column"]/div/div[7]')
        table_entries = table.text.split("\n")
        tickers = [x for x in table_entries if x.isupper() and ":" not in x]
        total_collected = len(tickers)

        b.quit()
        print("total collected = " + str(total_collected))
        return {
            "error": False,
            "total": len(tickers),
            "tickers": tickers,
        }

    b.quit()
    return {
        "error": True,
        "total": len(tickers),
        "tickers": {},
    }


def _get_sector(ticker):
    # All data is previously cleaned to always have a sector, no try needed.
    return ticker['sector']


def _get_sector_or_industry_count_from_summary(summary, sector_or_industry):
    try:
        return summary[sector_or_industry]
    except KeyError:
        return 0


def _get_industry(ticker):
    # All data is previously cleaned to always have a sector, no try needed.
    return ticker['industry']


def _get_dummy_ticker_dict(ticker):
    return {'ticker': ticker,
            'price': 'n/a',
            'sector': 'n/a',
            'industry': 'n/a',
            'exchange': 'n/a',
            'marketCap': 'n/a',
            'volume': 'n/a',
            'volume10Day': 'n/a',
            '52WeekChange': 'n/a',
            '52WeekHigh': 'n/a',
            '52WeekLow': 'n/a',
            '52HighLowDiff': 'n/a',
            'shortRatio': 'n/a',
            'companyName': 'n/a',
            'businessSummary': 'n/a',
            'previousClose': 'n/a',
            'marketOpen': 'n/a',
            '200Average': 'n/a',
            '50Average': 'n/a',
            'dayLow': 'n/a',
            'dayHigh': 'n/a',
            'allData': 'n/a'
            }


def _old_selenium_gather_highs_lows_performance_based(url, headless=True, linux=True):
    """
    This extracts from the actual table. It is cleaner, but is slower and barchart changed it's table so that
    scrapers can't select it anymore. Created new function based on scraping site text only.
    """
    initiated = True

    # Initiate the driver with url in a retry loop
    if headless:
        retry = 0
        while retry < 5:
            try:
                if retry != 0:
                    try:
                        b.quit()
                    except:
                        pass
                    time.sleep(3)
                b = cS.create_headless_driver_no_url(linux)
                b.set_page_load_timeout(60)
                b.get(url)
                break
            except:
                print("Failed initiating, retrying...")
                if retry == 4:
                    initiated = False
                retry = retry + 1
    else:
        retry = 0
        while retry < 5:
            try:
                if retry != 0:
                    time.sleep(3)
                b = cS.create_driver_no_url()
                b.set_page_load_timeout(60)
                b.get(url)
                break
            except:
                print("Failed initiating")
                if retry == 4:
                    initiated = False
                retry = retry + 1

    tickers = list()
    save_time = time.time()
    if initiated:
        first_row_check = '//*[@id="main-content-column"]/div/div[7]/div/div[2]/div/div/ng-transclude/' \
                          'table/tbody/tr[1]/td[2]/div'

        # Find out how many total tickers there are
        pagination_xpath = '//*[@id="main-content-column"]/div/div[7]/div/div[3]/div[1]'

        if cS.wait_for_page(b, first_row_check, 10):
            try:
                if cS.wait_for_page(b, pagination_xpath, 10, auto_quit_browser=False):
                    pag_text = b.find_element_by_xpath(
                        '//*[@id="main-content-column"]/div/div[7]/div/div[3]/div[1]').text
                    try:
                        total_stocks = int(pag_text.split("of")[1].strip())
                    except IndexError:
                        total_stocks = 0

                    if total_stocks % 100 != 0:
                        total_pages = math.ceil(total_stocks / 100)
                    else:
                        total_pages = int(total_stocks / 100)
                else:
                    total_pages = 1
            except:
                total_pages = 0
                pass

            x = 1
            total_collected = 0
            while x <= total_pages:
                if x == 1:
                    pass  # no need, already on page 1
                else:
                    temp_url = _construct_performance_url(url, x)

                    # Try the new page up to 5 times
                    retry = 0
                    while retry < 5:
                        try:
                            if retry != 0:
                                try:
                                    b.quit()
                                    time.sleep(3)
                                except:
                                    pass

                                if headless:
                                    b = cS.create_headless_driver_no_url(linux)
                                else:
                                    b = cS.create_driver_no_url()
                                b.set_page_load_timeout(60)

                            b.get(temp_url)
                            break
                        except:
                            print("Failed initiating, retrying...")
                            if retry == 4:
                                print("Failed to get page " + str(x) + ". Writing what is available and quitting.")

                                return {
                                    "error": True,
                                    "total": len(tickers),
                                    "tickers": {},
                                }
                            retry = retry + 1

                table_path = '//*[@id="main-content-column"]/div/div[7]/div/div[2]/div/div/ng-transclude/table/tbody/'
                first_ticker_load = table_path + 'tr[1]/td[1]/div/span[2]/a'

                if cS.wait_for_page(b, first_ticker_load, 10):
                    i = 1
                    while i < 101:
                        if i % 10 == 0:
                            current_time = time.time()
                            since_last = current_time - save_time
                            save_time = current_time
                            print(str(i) + " tickers collected...time lapse since last = " + str(since_last))
                        row_path = 'tr[' + str(i) + ']/'
                        ticker_path = table_path + row_path + 'td[1]/div/span[2]/a'

                        try:
                            tickers.append(b.find_element_by_xpath(ticker_path).text)
                        except:
                            total_collected = total_collected + i
                            break
                        i = i + 1

                x = x + 1

            b.quit()
            print("total collected = " + str(len(tickers)))
            return {
                "error": False,
                "total": len(tickers),
                "tickers": tickers,
            }
    else:
        print("Could not initiate selenium after 5 attempts. Exiting with error")
        try:
            b.quit()
        except:
            pass

        return {
            "error": True,
            "total": 0,
            "tickers": {},
        }

    b.quit()
    return {
        "error": True,
        "total": len(tickers),
        "tickers": {},
    }


def _selenium_gather_highs_lows_performance_based(url, headless=True, linux=True):
    """
    This function scrapes all the ticker text from the table. The old version selected each ticker element within
    the table, but that method was slower and barchart.com made that impossible to do. So now text selection is used.

    This method can become broken whenever barchart updates their table format.

    :param url:
    :param headless:
    :param linux:
    :return:
    """
    initiated = True

    # Initiate the driver with url in a retry loop
    if headless:
        retry = 0
        while retry < 5:
            try:
                if retry != 0:
                    try:
                        b.quit()
                    except:
                        pass
                    time.sleep(3)
                b = cS.create_headless_driver_no_url(linux)
                b.set_page_load_timeout(60)
                b.get(url)
                break
            except:
                print("Failed initiating, retrying...")
                if retry == 4:
                    initiated = False
                retry = retry + 1
    else:
        retry = 0
        while retry < 5:
            try:
                if retry != 0:
                    time.sleep(3)
                b = cS.create_driver_no_url()
                b.set_page_load_timeout(60)
                b.get(url)
                break
            except:
                print("Failed initiating")
                if retry == 4:
                    initiated = False
                retry = retry + 1

    tickers = list()
    save_time = time.time()
    if initiated:
        page_check = '//*[@id="main-content-column"]/div/div[7]/div/div[2]'

        # Find out how many total tickers there are
        pagination_xpath = '//*[@id="main-content-column"]/div/div[7]/div/div[3]/div[1]'

        if cS.wait_for_page(b, page_check, 10):
            try:
                if cS.wait_for_page(b, pagination_xpath, 10, auto_quit_browser=False):
                    pag_text = b.find_element_by_xpath(
                        '//*[@id="main-content-column"]/div/div[7]/div/div[3]/div[1]').text
                    try:
                        total_stocks = int(pag_text.split("of")[1].strip())
                    except IndexError:
                        total_stocks = 0

                    if total_stocks % 100 != 0:
                        total_pages = math.ceil(total_stocks / 100)
                    else:
                        total_pages = int(total_stocks / 100)
                else:
                    total_pages = 1
            except:
                total_pages = 0
                pass

            x = 1
            total_collected = 0
            while x <= total_pages:
                if x == 1:
                    pass  # no need, already on page 1
                else:
                    temp_url = _construct_performance_url(url, x)

                    # Try the new page up to 5 times
                    retry = 0
                    while retry < 5:
                        try:
                            if retry != 0:
                                try:
                                    b.quit()
                                    time.sleep(3)
                                except:
                                    pass

                                if headless:
                                    b = cS.create_headless_driver_no_url(linux)
                                else:
                                    b = cS.create_driver_no_url()
                                b.set_page_load_timeout(60)

                            b.get(temp_url)
                            break
                        except:
                            print("Failed initiating, retrying...")
                            if retry == 4:
                                print("Failed to get page " + str(x) + ". Writing what is available and quitting.")

                                return {
                                    "error": True,
                                    "total": len(tickers),
                                    "tickers": {},
                                }
                            retry = retry + 1

                if cS.wait_for_page(b, page_check, 10):
                    page_text = b.find_element_by_xpath('//*[@id="main-content-column"]/div/div[7]/div/div[2]').text
                    page_list = page_text.split("\n")
                    i = 11
                    while i < 1012:  # header row + 100 symbols per page, 11 columns per ticker
                        try:
                            ticker = page_list[i]
                            tickers.append(ticker)
                            total_collected = total_collected + 1
                        except:
                            # page is complete
                            break

                        i = i + 10

                x = x + 1

            b.quit()
            print("total collected = " + str(len(tickers)))
            return {
                "error": False,
                "total": len(tickers),
                "tickers": tickers,
            }
    else:
        print("Could not initiate selenium after 5 attempts. Exiting with error")
        try:
            b.quit()
        except:
            pass

        return {
            "error": True,
            "total": 0,
            "tickers": {},
        }

    b.quit()
    return {
        "error": True,
        "total": len(tickers),
        "tickers": {},
    }


def _construct_url_for_selenium(time_frame, price_type):
    base_url = "https://www.barchart.com/stocks/highs-lows"
    time_frame_url = "timeFrame="

    if time_frame == 1:
        time_par = '1m'
    elif time_frame == 3:
        time_par = '3m'
    elif time_frame == 6:
        time_par = '6m'
    elif time_frame == 12:
        time_par = '1y'
    else:
        return "Error in time_frame. Must be int: 1, 2, 6, or 12"

    if price_type == "high":
        url = base_url + "?" + time_frame_url + time_par + "&page=all"
    elif price_type == "low":
        url = base_url + "/lows?" + time_frame_url + time_par + "&page=all"
    else:
        return "Error in price type. Try 'high' or 'low'"

    return url


def _construct_performance_url(page_url, page_number):
    page_number = str(page_number)
    return page_url + '&page=' + page_number


def _test_archive():
    selenium_performance_based_stocks_on_highs_and_lows(linux=False, save="temp.json")
    start = time.time()
    selenium_retrieve_stocks_on_highs_and_lows(save="temp.json")
    end = time.time()
    print("total time:" + str(end - start))


def check_bar_chart_file_for_no_errors(full_path_file):
    """
    This function checks a raw data file created by one of the following:
        _selenium_gather_highs_lows
        _selneium_gather_highs_lows_performance_based

    It then checks if there were any errors in the file

    :param full_path_file:
    :return: bool(), True if no errors, False if errors
    """

    d = fC.load_json_from_file(full_path_file)

    frames = [d['1month'], d['3month'], d['6month'], d['12month']]
    for frame in frames:
        high_errors = frame['highs']['error']
        low_errors = frame['lows']['error']
        if high_errors:
            return False
        if low_errors:
            return False

    return True


def _test_parsing():
    cur_dir = osC.get_working_dir()
    parent_dir = osC.get_parent_dir_given_full_dir(cur_dir)
    bar_chart_dir = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks',
                                                   'barchart_high-lows'], list=1)
    bar_chart_file = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks',
                                                    'barchart_high-lows', 'bc-high-lows_20211218104724.json'], list=1)

    bc = BarChartHighLowAnalysis(archive_directory_path=bar_chart_dir)
    stop = 1


def _test_check_bar_chart_for_errors():
    cur_dir = osC.get_working_dir()
    parent_dir = osC.get_parent_dir_given_full_dir(cur_dir)
    bar_chart_dir = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks',
                                                   'barchart_high-lows'], list=1)
    bar_chart_file = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks',
                                                    'barchart_high-lows', 'bc-high-lows_20220104173002.json'], list=1)
    print(check_bar_chart_file_for_no_errors(bar_chart_file))


def _test_analysis():
    cur_dir = osC.get_working_dir()
    parent_dir = osC.get_parent_dir_given_full_dir(cur_dir)
    bar_chart_dir = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks',
                                                   'barchart_high-lows'], list=1)

    bc = BarChartHighLowAnalysis(archive_directory_path=bar_chart_dir, use_recent_cache=True)
    nem_data = bc.get_ticker_data_from_recent_cache("NEM")
    print(bc.dates)
    # bc.clean_recent_cache(report_status_only=True)
    # bc.update_parsed_files_na()
    stop = 1

    stop = 1
    # report = bc.report_on_parsed_data()
    # bar_chart_file = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks', 'barchart_high-lows', 'bc-high-lows_20220104173002.json'], list=1)
    #


def _test_update_recent_cache():
    cur_dir = osC.get_working_dir()
    parent_dir = osC.get_parent_dir_given_full_dir(cur_dir)
    bar_chart_dir = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks',
                                                   'barchart_high-lows'], list=1)
    bc = BarChartHighLowAnalysis(archive_directory_path=bar_chart_dir, use_recent_cache=True)
    # bc.update_recent_cache(no_value_only=True)
    bc.update_recent_cache(report_only=True)


def _test_class_with_grind_sunday_archive():
    """
    The grindSundayStocks location has a complete archive for use in testing the function.
    :return:
    """

    pc_dir = osC.create_root_path_starting_from_drive("C:")
    bc_dir = osC.append_to_dir(pc_dir, ["Users", "heide", "Documents", "Luke", "Programming", "grindSundayStocks",
                                        "resources", "grindSundayStocks", "barchart_high-lows"], list=True)
    stop = 1

    """
    Get week bounds (this report is designed to run on weekend, so it gets the bounds for the prior trade wk)
    Then load the BC object for that week
    """
    d = tC.get_date_today(return_string=True, str_format="%Y%m%d")
    week_find_date = tC.add_days_to_date(d, -4, input_format="%Y%m%d").replace("-", "")
    week_bounds = tC.get_week_start_and_week_end_dates_for_date(week_find_date)
    week_start = week_bounds["weekStart"]
    week_end = tC.add_days_to_date(week_bounds["weekEnd"], -2, input_format="%Y%m%d",
                                   output_format="%Y%m%d")


    bc = BarChartHighLowAnalysis(archive_directory_path=bc_dir, start_date=week_start,
                                 end_date=week_end, date_format="%Y%m%d")
    s_list = bc.no_dc_get_stock_list_given_parameters(sectors="consumer defensive")
    i_list = bc.no_dc_get_stock_list_given_parameters(industries="biotechnology")

    s_list2 = bc.no_dc_get_stock_list_given_parameters(sectors=["consumer defensive", "technology"])
    i_list2 = bc.no_dc_get_stock_list_given_parameters(industries=["biotechnology", "gambling"])
    tester = 2
    all_sectors = bc.all_sectors
    stop = 1
    stop2 = 1


if __name__ == '__main__':
    bc_collect = BarChartDataCollection(headless_collection=False)
    bc_collect.retrieve_stocks_high_lows()
    _test_class_with_grind_sunday_archive()
    stop = 1
    # _test_check_bar_chart()
    # _test_analysis()
    # _test_update_recent_cache()


