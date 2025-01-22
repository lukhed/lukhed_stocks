from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import mathCommon as mC


def normalize_prices_to_percent_gain(list_of_prices, start_at_zero=True, raw_percent=False):
    """
    To plot stocks on the same graph, they need to be normalized to percent gains. This function normalizes prices
    to percent gains from the first value in the list.

    :param list_of_prices:
    :param start_at_zero:   bool(), by default starts at 0, but can also start at 1 if false
    :param raw_percent:     bool(), raw if you want raw percent (e.g. 0.5 = 50%) or whole to
                            multiple by 100 (50 = 50%)
    :return:                list(), normalized price (percents as floats)
    """

    if raw_percent:
        m = 1
    else:
        m = 100

    if start_at_zero:
        return [mC.pretty_round_function((x/list_of_prices[0] - 1)*m, 4) for x in list_of_prices]
    else:
        return [mC.pretty_round_function((x/list_of_prices[0])*m, 4) for x in list_of_prices]


def normalize_y_axis_to_percent_in_df(df):
    return df / df.iloc[0, :]


def calculate_hypothetical_equity(price_list, starting_equity):
    """
    Given a list of prices of any ticker, and a starting equity, calculate your hypothetical equity over time as
    if you bought the ticker with the starting equity.

    :param price_list:
    :param starting_equity:
    :return:
    """
    start_quantity = mC.pretty_round_function(starting_equity / price_list[0])
    equity_list = [mC.pretty_round_function(x * start_quantity) for x in price_list]

    return equity_list


def check_mark_minervini_trend_template(ticker, return_full_details=False, schwab_api=None,
                                        include_criteria_descriptions=False, provide_schwab_quote=None):
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


def calculate_moving_average_indicators(ticker, ma_period_type="day", return_setting="full"):
    """

    :param ticker:
    :param ma_period_type:
    :param return_setting:
    :return:
    """

    close_prices = list()
    self._parse_api_delay()
    if ma_period_type.lower() == "day":
        day_data = self.api.get_price_history_every_day(ticker).json()
        close_prices = [x["close"] for x in day_data["candles"]]
    else:
        day_data = None
    try:
        list_10 = mC.simple_moving_average_given_list(close_prices, 10)
        last_10 = list_10[len(list_10) - 1]
    except:
        list_10 = None
        last_10 = None
    try:
        list_20 = mC.simple_moving_average_given_list(close_prices, 20)
        last_20 = list_20[len(list_20) - 1]
    except:
        list_20 = None
        last_20 = None
    try:
        list_50 = mC.simple_moving_average_given_list(close_prices, 50)
        last_50 = list_50[len(list_50) - 1]
    except:
        list_50 = None
        last_50 = None
    try:
        list_100 = mC.simple_moving_average_given_list(close_prices, 100)
        last_100 = list_100[len(list_100) - 1]
    except:
        list_100 = None
        last_100 = None
    try:
        list_150 = mC.simple_moving_average_given_list(close_prices, 150)
        last_150 = list_150[len(list_150) - 1]
    except:
        list_150 = None
        last_150 = None
    try:
        list_200 = mC.simple_moving_average_given_list(close_prices, 200)
        last_200 = list_200[len(list_200) - 1]
    except:
        list_200 = None
        last_200 = None


    op_dict = {
        "sma10Last": last_10,
        "sma10Points": list_10,
        "sma20Last": last_20,
        "sma20Points": list_20,
        "sma50Last": last_50,
        "sma50Points": list_50,
        "sma100Last": last_100,
        "sma100Points": list_100,
        "sma150Last": last_150,
        "sma150Points": list_150,
        "sma200Last": last_200,
        "sma200Points": list_200,
        "allHistory": day_data
    }

    return op_dict


if __name__ == '__main__':
    normalized = normalize_prices_to_percent_gain([1, 1.20, 1.30, 1.50, 1.75, 2])
    test = 1
