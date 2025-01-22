from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import timeCommon as tC
from resources.aceCommon import listWorkCommon as lC
from resources.aceCommon import mathCommon as mC
import yfinance as yf
import commonMatplotLineChart
import commonMatplotFormatting

"""
Custom wrapper for working with yfinance API
https://github.com/ranaroussi/yfinance
https://aroussi.com/post/python-yahoo-finance
"""


class YahooFinance:
    def __init__(self, live_cache=True, add_api_delay=False):
        """
        :param live_cache:    bool(), If true, each functionality that supports live cache will be turned on. Current
                              functions supporting live_cache:
                                    Each ticker called will have a summary loaded into self.ticker-summaries_cache.
                                    This will be a dictionary so you can retrieve basic info about the stock from cache
                                    instead of making a new call.

        :param add_api_delay: bool(), if True, all calls to YahooFinance will have a 1 second delay automatically
                              programmed in. This is useful for when you have a function that will call the api
                              many times. The delay will only be applied when using the api (not cache)
        """

        if add_api_delay:
            self.delay = 1
        else:
            self.delay = None
        self.live_cache = live_cache
        self.ticker_summary_cache = dict()      # cache recent calls here

    def plot_ticker(self, ticker, provide_obj=None, time_period='1mo', start_date=None, end_date=None,
                    time_interval='1d', price_type='Close', show_plot=True, save_location=None):
        """
        This function uses matplotlib to plot a time series from yfinance object
        :param ticker: str(), ticker symbol
        :param provide_obj: optional, yfinance ticker object
        :param time_period: str(), valid periods are 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        :param start_date: str(), optional if preferred over time period YYYY-MM-DD
        :param end_date: str(), optional if preferred over time period; YYYY-MM-DD
        :param time_interval: str(), valid intervals are 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        :param price_type: str(), type of price to plot, 'Close' by default, 'Open' options.
        :param show_plot: bool(), if True, will show the plot created
        :param save_location: optional, provide a path to save the figure if you want to save it.
        :return: dict(), with plot figure and related axis data.
        """

        ticker_name = ticker
        ticker = self._parse_basic_ticker_input(ticker, provide_obj=provide_obj)

        # Actions provides things like dividends and stock splits in the dataframe
        if start_date is None:
            price_history = ticker.history(period=time_period, interval=time_interval, actions=False)
        else:
            price_history = ticker.history(start=start_date, end=end_date, interval=time_interval, actions=False)

        df = price_history[price_type]
        plot_dict = commonMatplotLineChart.create_line_chart_from_data_frame(df)
        ax = plot_dict["ax"]
        test = 1

    def ticker_get_history(self, ticker, provide_obj=None, price_type="Close", return_type="df",
                           return_time_format=None, defined_period=None, start_date=None, end_date=None,
                           date_format="%Y%m%d", interval=None, include_actions=False):
        """
        If no parameters are provided, max history will be obtained.

        Note about the yahoo API: the history method returns adjusted close data within the close column. The
        download method returns the close data in the close column. So the download method is used here.

        :param ticker:              str(), ticker for which you want data

        :param provide_obj:         optional, yfinance ticker object

        :param price_type:          optional, str(), Open, Close, High, Low, Volume

        :param return_type:         optional, str(), default is pandas dataframe
                                                     df = pandas dataframe
                                                     lists = return is tuple of x, y lists

        :param return_time_format:  optional, str(), default is the date time yahoo provides, else provide a time
                                    format. E.g. "%Y%m%d"

                                    Note: This will only apply to return_type = lists

        :param defined_period:      optional, str(), use for easy definition. Options are:
                                    1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

        :param start_date:          optional, str(), start date in which to begin download. Only used if defined_period
                                    is not used.

        :param end_date:            optional, str(), end date in which to end download. Only use if defined_period
                                    is not used.

        :param date_format:         optional, str(), if dates provided, specify the format in which they are provided

        :param interval:            optional, str(), interval for which data points are provided in. Default is 1 day.
                                    Options are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

        :param include_actions:     optional, bool(), Download stock dividends and stock splits events.
        :return:                    data for ticker as specified
        """

        # ticker = self._parse_basic_ticker_input(ticker, provide_obj=provide_obj)
        if interval is None:
            interval = "1d"

        if start_date is not None:
            start_date = tC.convert_date_format(start_date, date_format=date_format, to_format="%Y-%m-%d")

        if end_date is None:
            end_date = tC.get_date_today(return_string=True, str_format="%Y-%m-%d")
        else:
            end_date = tC.convert_date_format(end_date, date_format=date_format, to_format="%Y-%m-%d")
            end_date = tC.add_days_to_date(end_date, 1, input_format="%Y-%m-%d")

        if defined_period is not None:
            price_history = yf.download(ticker, period=defined_period, interval=interval, actions=include_actions,
                                        progress=False)
        elif start_date is not None:
            price_history = yf.download(ticker, start=start_date, end=end_date, interval=interval,
                                        actions=include_actions, progress=False)
        else:
            price_history = yf.download(ticker, interval=interval, actions=include_actions,
                                        progress=False)

        df = price_history[price_type]

        if return_type == "lists":
            x, y = mC.data_frame_to_x_y_list(df)
            if return_time_format is not None:
                x = [tC.convert_date_time_to_string(i, return_time_format) for i in x]
            return x, y
        else:
            return df


    def ticker_get_all_yf_data(self, ticker):
        """
        This function is the basis for many other functions. It utilizes the yfinance "Ticker" interface to retrieve
        ticker information for the given symbol. It also

        :param ticker: str(), e.g. AAPL
        :return: yfinance ticker object
        """
        try:
            res = yf.Ticker(ticker)
            if self.delay is not None:
                tC.sleep(self.delay)
            success = True
        except:
            res = 'error'
            success = False

        if self.live_cache:
            if success:
                self.ticker_summary_cache.update(
                    {
                        ticker:
                            {"summary": self.ticker_get_summary(ticker, provide_obj=res),
                             "success": success
                             }
                    })
            else:
                self.ticker_summary_cache.update(
                    {
                        ticker:
                            {"summary": {},
                             "success": success
                             }
                    })

        return res

    def ticker_get_summary(self, ticker, provide_obj=None, include_all_data=False, try_live_cache=False):
        """
        This function compiles all data available in individual ticker functions into a summary dictionary. If you
        need more than one piece of information for a specific ticker, this function should be utilizes instead
        of calling each individual function, as it is most efficient with API requests.

        :param ticker: str(), ticker symbol
        :param provide_obj: optional yfinance ticker object (if provided, yfinance api doesn't need to be called to get
                            ticker information)
        :param include_all_data: bool(), if True, will return the full yfinance object in the dictionary in key
                                 'allData'
        :param try_live_cache: bool(), if True, will search the live cache before retrieving a ticker. This should be
                               used when most up to date price is not needed (for example, when looking for sectors)
                               or when you are searching a large list of stocks that may have repeats.
                               Note: The live cache feature must be on (class instantiated with live_cache=True)
        :return: dict(), ticker summary
        """

        ticker_name = ticker

        cache_flag = False
        cache_summary = {}
        if try_live_cache and self.live_cache:
            cache_summary = self._try_live_cache_summary(ticker_name)
            if cache_summary is not None:
                cache_flag = True

        if cache_flag:
            return cache_summary
        else:
            ticker = self._parse_basic_ticker_input(ticker, provide_obj)

            if include_all_data:
                yf_obj = ticker
            else:
                yf_obj = False

            return {
                "ticker": ticker_name,
                "price": self.ticker_get_price(ticker_name, provide_obj=ticker),
                "sector": self.ticker_get_sector(ticker_name, provide_obj=ticker),
                "industry": self.ticker_get_industry(ticker_name, provide_obj=ticker),
                "exchange": self.ticker_get_exchange(ticker_name, provide_obj=ticker),
                "marketCap": self.ticker_get_marketcap(ticker_name, provide_obj=ticker),
                "volume": self.ticker_get_day_volume(ticker_name, provide_obj=ticker),
                "averageVolume": self.ticker_get_average_volume(ticker_name, provide_obj=ticker),
                "volume10Day": self.ticker_get_volume_ten_day(ticker_name, provide_obj=ticker),
                "52WeekChange": self.ticker_52wk_change(ticker_name, provide_obj=ticker),
                "52WeekHigh": self.ticker_get_52wk_high(ticker_name, provide_obj=ticker),
                "52WeekLow": self.ticker_get_52wk_low(ticker_name, provide_obj=ticker),
                "52HighLowDiff": self.ticker_get_percent_diff_52wk_high_low(ticker_name, provide_obj=ticker),
                "shortRatio": self.ticker_get_short_ratio(ticker_name, provide_obj=ticker),
                "companyName": self.ticker_get_company_name(ticker_name, provide_obj=ticker),
                "businessSummary": self.ticker_get_business_summary(ticker_name, provide_obj=ticker),
                "previousClose": self.ticker_get_price_previous_close(ticker_name, provide_obj=ticker),
                "marketOpen": self.ticker_get_price_open(ticker_name, provide_obj=ticker),
                "200Average": self.ticker_200d_average(ticker_name, provide_obj=ticker),
                "50Average": self.ticker_50d_average(ticker_name, provide_obj=ticker),
                "dayLow": self.ticker_get_day_low(ticker_name, provide_obj=ticker),
                "dayHigh": self.ticker_get_day_high(ticker_name, provide_obj=ticker),
                "allData": yf_obj
            }

    def ticker_get_sector(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['sector']
        except:
            return "n/a"

    def ticker_get_industry(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['industry']
        except:
            return "n/a"

    def ticker_get_exchange(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['exchange']
        except:
            return "n/a"

    def ticker_get_marketcap(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['marketCap']
        except:
            return "n/a"

    def ticker_get_volume_ten_day(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['averageDailyVolume10Day']
        except:
            return "n/a"

    def ticker_get_average_volume(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['averageVolume']
        except:
            return "n/a"

    def ticker_get_52wk_high(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['fiftyTwoWeekHigh']
        except:
            return "n/a"

    def ticker_get_52wk_low(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['fiftyTwoWeekLow']
        except:
            return "n/a"

    def ticker_get_percent_diff_52wk_high_low(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return (ticker.info['fiftyTwoWeekHigh'] - ticker.info['fiftyTwoWeekLow']) / ticker.info['fiftyTwoWeekHigh']
        except:
            return "n/a"

    def ticker_get_short_ratio(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['shortRatio']
        except:
            return "n/a"

    def ticker_get_business_summary(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['longBusinessSummary']
        except:
            return "n/a"

    def ticker_get_price(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['currentPrice']
        except:
            return "n/a"

    def ticker_get_price_previous_close(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['regularMarketPreviousClose']
        except:
            return "n/a"

    def ticker_get_price_open(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['regularMarketOpen']
        except:
            return "n/a"

    def ticker_get_company_name(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['longName']
        except:
            return "n/a"

    def ticker_52wk_change(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['52WeekChange']
        except:
            return "n/a"

    def ticker_200d_average(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['twoHundredDayAverage']
        except:
            return "n/a"

    def ticker_50d_average(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['fiftyDayAverage']
        except:
            return "n/a"

    def ticker_get_day_low(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['regularMarketDayLow']
        except:
            return "n/a"

    def ticker_get_day_high(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['regularMarketDayHigh']
        except:
            return "n/a"

    def ticker_get_day_volume(self, ticker, provide_obj=None):
        ticker = self._parse_basic_ticker_input(ticker, provide_obj)
        try:
            return ticker.info['regularMarketVolume']
        except:
            return "n/a"

    def _parse_basic_ticker_input(self, ticker, provide_obj):
        """
        This function parses all basic input of ticker and provide_obj. This allows for more flexibility in managing
        spamming the service.

        :param ticker: str(), ticker symbol
        :param provide_obj: None or yfinance object
        :return: yfinance ticker object
        """
        if provide_obj is None:
            return self.ticker_get_all_yf_data(ticker)
        else:
            return provide_obj

    def _try_live_cache_summary(self, ticker):
        try:
            return self.ticker_summary_cache[ticker.upper()]['summary']
        except KeyError:
            return None


def get_sector_given_industry(industry, provide_cache=False, get_cache_only=False):
    """
    Provide an industry and get the associated sector. The mapping must be kept updated at the file location:
    ['resources', 'commonStocks', 'stockClassification', 'yahooSectorToIndustry.csv']

    If this function is to be called many times in one program, then use the cache mechanism by first invoking the
    function with "get_cache_only=True". The function will return a list. Then provide that list back to the function
    in the "provide_cache" parameter each time you want to use the function. This way, the file that is used to
    map the sector to industry is only called one time.

    :param industry:        str(), industry you want the sector for, not case sensitive
    :param provide_cache:   list(), list of list which is obtained by first using "get_cache_only".
                            See description there.
    :param get_cache_only:  bool(), If true, this function will  ignore industry input and just return the list of list
                            that is used for mapping. This list of list provided would then be used for all future
                            calls to this function so that the function is using the cache instead of opening and
                            closing the file several times.
    :return:
    """

    f = osC.create_file_path_string(['resources', 'commonStocks', 'stockClassification', 'yahooSectorToIndustry.csv'])

    if provide_cache is not False:
        cache = provide_cache
    else:
        cache = fC.return_lines_in_file(f, header="no")
    if get_cache_only:
        return cache

    for x in cache:
        if industry.lower() == x[1].lower():
            return x[0]

    return "no match"


def get_industry_list_for_given_sector(sector):
    f = osC.create_file_path_string(['resources', 'commonStocks', 'stockClassification', 'yahooSectorToIndustry.csv'])
    cache = fC.return_lines_in_file(f, header="no")

    return [x[1] for x in cache if x[0].lower() == sector.lower()]


def get_proper_case_for_industry_or_sector(string_to_fix, provide_cache=False, get_cache_only=False):
    """
    This function is used for getting the correct case for case sensitive dictionary searches on a sector or
    industry. For example, if a user puts "technology" into the sector input, this would return "Technology".

    :param string_to_fix:   str(), string to correct case wise.
    :param provide_cache:   list(), list of list which is obtained by first using "get_cache_only".
                            See description there.
    :param get_cache_only:  bool(), If true, this function will  ignore industry input and just return the list of list
                            that is used for mapping. This list of list provided would then be used for all future
                            calls to this function so that the function is using the cache instead of opening and
                            closing the file several times.
    :return:                str(), with proper case
    """

    f = osC.create_file_path_string(['resources', 'commonStocks', 'stockClassification', 'yahooSectorToIndustry.csv'])

    if provide_cache is not False:
        cache = provide_cache
    else:
        cache = fC.return_lines_in_file(f, header="no")
    if get_cache_only:
        return cache

    for x in cache:
        if string_to_fix.lower() == x[0].lower():
            return x[0]
        if string_to_fix.lower() == x[1].lower():
            return x[1]

    return "no match"


def get_industry_counts_given_stock_list(ticker_list):
    """
    This function takes in a list of yahoo ticker dictionaries (list of stocks after api fetches them) and creates
    an industry summary given the list.

    :param ticker_list: list()
    :return: dict(), industry summary
    """

    industry_list = list()
    for ticker in ticker_list:
        try:
            temp_industry = ticker['industry']
        except KeyError:
            temp_industry = "n/a"

        industry_list.append(temp_industry)

    unique_industries = lC.return_unique_values(industry_list)

    op_dict = {}
    for ui in unique_industries:
        op_dict.update({ui: industry_list.count(ui)})

    return op_dict


def get_industry_list_given_stock_list(ticker_list):
    industry_list = list()
    for ticker in ticker_list:
        try:
            temp_industry = ticker['industry']
        except KeyError:
            temp_industry = "n/a"

        industry_list.append(temp_industry)

    return industry_list


def add_sector_industry_pair_to_mapping(sector, industry):
    f = osC.create_file_path_string(['resources', 'commonStocks', 'stockClassification', 'yahooSectorToIndustry.csv'])
    cache = fC.return_lines_in_file(f)

    # first check if pair already exists
    for x in cache:
        if x[0].lower() == sector and x[1].lower() == industry:
            return "pair already exists, no updates made"

    cache.append([sector, industry])

    fC.write_list_of_list_to_csv(f, cache)


def update_sector_to_industry_mapping_based_on_bc_archive(full_path_to_archive):
    """
    This function looks at a barchart archive that was created, gets all the industries in that file, and makes
    sure the industry to sector mapping file has that industry (will add new mappings if found)
    :return:
    """
    import commonStocksBarChart
    bc = commonStocksBarChart.BarChartHighLowAnalysis(archive_directory_path=full_path_to_archive)
    cache = get_sector_given_industry("", get_cache_only=True)
    break_all = 0
    for i in bc.all_industries:
        if get_sector_given_industry(i, provide_cache=cache) == "no match":
            for d in bc.data:
                if break_all == 1:
                    break
                checks = [d['data']['1month']['highs']['tickers'], d['data']['1month']['lows']['tickers']]
                for c in checks:
                    if break_all == 1:
                        break
                    for t in c:
                        if t['industry'] == i:
                            i_pair = i
                            s_pair = t['sector']
                            break_all = 1
                            break
        if break_all == 1:
            add_sector_industry_pair_to_mapping(s_pair, i_pair)
            print("pair added: " + s_pair + " : " + i_pair)
            break_all = 0


def run_update_of_mapping():
    cur_dir = osC.get_working_dir()
    parent_dir = osC.get_parent_dir_given_full_dir(cur_dir)
    bar_chart_dir = osC.append_to_dir(parent_dir, ['grindSundayStocks', 'resources', 'grindSundayStocks',
                                                   'barchart_high-lows'], list=1)
    update_sector_to_industry_mapping_based_on_bc_archive(bar_chart_dir)


def testing():
    y = YahooFinance()
    tick = y.ticker_get_summary("CRWD", try_live_cache=True)
    stop = 1
    # df = y.ticker_get_history("SPY", return_type="df", return_time_format="%Y%m%d")
    stop = 1
    # y.plot_ticker("AAPL")
    # tick_summary = y.ticker_get_summary("AAPL", try_live_cache=True)
    stop = 1


if __name__ == '__main__':
    testing()
    # run_update_of_mapping()

