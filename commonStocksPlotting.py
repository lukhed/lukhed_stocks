import commonMatplotFormatting
from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
import commonMatplotLineChart as lineChart
import commonMatplotFormatting as formatChart
import commonMatplotBasic as basicChart
from commonMatplotWrapper import ActivePlotting
import commonStocksYahooApi
import commonStocksTdApi
import commonStocksCalculations

"""
Note: This module requires the separate project commonMatplot before working
"""


class StockPlotting(ActivePlotting):
    def __init__(self, api_obj=None, api_name="yahoo", console_led_plotting=False):
        """
        You can specify the API you want to start the class with. If none is specified, yahoo is chosen.

        Note: You can use "change_api" function to switch between services

        :param api_obj:         obj api, you can pass an actual Yahoo or TDA api
        :param api_name:        str(), if api_obj is not specified. Supported: "tda", "yahoo"
        """
        ActivePlotting.__init__(self)
        self.api_name = api_name.lower()
        self._parse_api_inputs(api_obj, api_name)
        if console_led_plotting:
            self._console_led_plotting()

    def _set_api_to_yahoo(self):
        self.api = commonStocksYahooApi.YahooFinance(live_cache=False, add_api_delay=True)
        self.api_name = "yahoo"

    def _set_api_to_tda(self):
        self.api = commonStocksYahooApi.YahooFinance(live_cache=False, add_api_delay=True)
        self.api_name = "tda"

    def _parse_api_inputs(self, api_obj, api_name):
        api_name = api_name.lower()
        if api_obj is None:
            api_name = api_name.lower()
            if api_name == "tda":
                self._set_api_to_tda()
            elif api_name == "yahoo":
                self._set_api_to_yahoo()
            else:
                print("Warning: you passed unsupported API arguments, defaulting to Yahoo.")
                self._set_api_to_yahoo()

        else:
            self.api_name = api_name.lower()
            self.api = api_obj

    def _console_led_plotting(self):
        gt = input("What type of graph? (line): ")
        if gt == "line":
            t = input("Type the ticker: ")
            p = input("Type the period: ")
            self.add_ticker_to_line_graph(t, p)

        i = "a"
        while i != "q":
            i = input("Show? y/n: ")
            if i == 'y':
                self.show_active_fig()

    def add_ticker_to_line_graph(self, ticker, defined_period=None, start_date=None, end_date=None,
                                 date_format="%Y%m%d", interval=None, y_unit="$", custom_label=None, line_color="blue"):
        """

        :param ticker:              str(), stock you want to plot.

        :param defined_period:      optional, str(), use for easy definition. Options are:
                                    1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        :param start_date:
        :param end_date:
        :param date_format:
        :param interval:            optional, str(), interval for which data points are provided in. Default is 1 day.
                                    Options are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        :param y_unit:              optional, str(), options are: $, %
        :param custom_label:
        :param line_color:          str(), color supported by matplot
        :return:
        """

        ticker = ticker.upper()
        if custom_label is None:
            label = ticker
        else:
            label = custom_label

        x, y = self.api.ticker_get_history(label, defined_period=defined_period, interval=interval,
                                           return_type="lists", return_time_format="%b %d, %Y", start_date=start_date,
                                           end_date=end_date, date_format=date_format)

        if y_unit == "%":
            y = commonStocksCalculations.normalize_prices_to_percent_gain(y)

        self.add_to_line_graph(x, y, ticker, color=line_color)

        # Some auto formatting based on experience
        if defined_period == "1y":
            self.active_fig_adjust_axis_major_ticks_by_specified_segments(12)
        elif defined_period == "2y":
            self.active_fig_adjust_axis_major_ticks_by_specified_segments(24)
        elif defined_period == "3y":
            self.active_fig_adjust_axis_major_ticks_by_specified_segments(36)
        elif defined_period == "5y":
            self.active_fig_adjust_axis_major_ticks_by_specified_segments(60)
        elif defined_period == "10y" or defined_period == "max":
            self.active_fig_adjust_axis_major_ticks_by_time_interval("year")

        if y_unit == "%":
            self.format_active_fig_add_percent_symbols_to_axis("y")

        self.active_fig_auto_format_dates()

    def add_titles(self, title, x_title, y_title):
        self.format_active_fig_add_title_to_subplot(title, title_size=18)
        self.format_active_fig_add_title_to_axis(y_title, "y", title_size=14)
        self.format_active_fig_add_title_to_axis(x_title, "x", title_size=14)

    def quick_formatting(self):
        self.format_active_fig_grid_on()
        self.format_active_fig_show_legend()

    def change_api(self, api_name, api_obj=None):
        """
        Specify a supported api.
        :param api_name:            str(), name of the api you are changing to (must be supported)
        :param api_obj:              optional, api object
        :return:                    None, sets the class api to the the specified api
        """

        self._parse_api_inputs(api_obj, api_name)



if __name__ == '__main__':
    # sp = StockPlotting(console_led_plotting=True)     # Make a common class for this
    # stop = 1
    sp = StockPlotting()
    sp.add_ticker_to_line_graph("SPY", defined_period="1mo")
    sp.add_titles("SPY Month Chart", "Date", "Price of SPY $")
    sp.add_ticker_to_line_graph("QQQ", defined_period="1mo")
    sp.show_active_fig()
    sp.start_new_fig()
    sp.add_ticker_to_line_graph("BOX", "1mo")
    stop = 1
    # sp.active_fig_adjust_axis_major_ticks_by_specified_segments(20)
    stop = 1
