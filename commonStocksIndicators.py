from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC
from resources.aceCommon import timeCommon as tC
from resources.aceCommon import mathCommon as mC
import commonStocksTdApi
import commonStocksYahooApi


def ibd_relative_strength(ticker, data_source="tda", provided_history=None, source_object=None):
    """
    https://www.youtube.com/watch?v=CdFmuCRq2tM

    Algorithm:
    Calculate strength as such:
        (% change last 63 days)*2 +
        (% change last 126 days) +
        (% change last 189 days) +
        (% change last 252 days)

    Rank stocks by strength, and percentile of rank is the rating (0 - 1)

    :param ticker:          str(), ticker for which you want the raw ranking value to be returned
    :param data_source:     str(), "tda" or "yahoo"
    :param provided_history dict(), if you already retrieved the history from tda or yahoo, then you can pass it here
                            so that it is not needed to call the service again.
    :param source_object:   object, supply the tda object if service is tda or yahoo object is source is yahoo
    :return:
    """

    today = tC.create_time_stamp_new(output_format="%Y%m%d")
    history_end = tC.add_days_to_date(today, -425, input_format="%Y%m%d", specify_string_format="%Y%m%d")

    last_price = float()
    price_minus_63 = float()
    price_minus_126 = float()
    price_minus_189 = float()
    price_minus_252 = float()

    weighted_change_63 = float()        # Weighted x2
    change_126 = float()
    change_189 = float()
    change_252 = float()

    if data_source == "tda":
        if source_object is None:
            td = commonStocksTdApi.Td(add_api_delay=True, keep_cache=True)
        else:
            td = source_object

        if provided_history is None:
            try:
                ticker_history = td.get_price_history(ticker, "day", from_date=history_end, to_date=today,
                                                      date_format_provided="%Y%m%d", convert_date_times=False)
            except:
                return None
        else:
            ticker_history = provided_history

        if ticker_history['empty']:
            return None
        elif len(ticker_history["candles"]) < 252:
            return "n/a"
        else:
            candles = ticker_history["candles"]
            last_price = candles[len(candles) - 1]['close']
            price_minus_63 = candles[len(candles) - 63]['close']
            price_minus_126 = candles[len(candles) - 126]['close']
            price_minus_189 = candles[len(candles) - 189]['close']
            price_minus_252 = candles[len(candles) - 252]['close']
            weighted_change_63 = mC.calculate_percent_change(price_minus_63, last_price) * 2
            change_126 = mC.calculate_percent_change(price_minus_126, last_price)
            change_189 = mC.calculate_percent_change(price_minus_189, last_price)
            change_252 = mC.calculate_percent_change(price_minus_252, last_price)
    elif data_source == "yahoo":
        if source_object is None:
            yahoo = commonStocksYahooApi.YahooFinance()
        else:
            yahoo = source_object
        try:
            ticker_history = yahoo.ticker_get_history(ticker, start_date=history_end, end_date=today,
                                                      date_format="%Y%m%d", price_type="Close", return_type="lists")
            candles = ticker_history[1]
            dates = ticker_history[0]
        except:
            return None

        if len(candles) < 252:
            return "n/a"

        last_price = candles[len(candles) - 1]
        price_minus_63 = candles[len(candles) - 63]
        price_minus_126 = candles[len(candles) - 126]
        price_minus_189 = candles[len(candles) - 189]
        price_minus_252 = candles[len(candles) - 252]
        weighted_change_63 = mC.calculate_percent_change(price_minus_63, last_price) * 2
        change_126 = mC.calculate_percent_change(price_minus_126, last_price)
        change_189 = mC.calculate_percent_change(price_minus_189, last_price)
        change_252 = mC.calculate_percent_change(price_minus_252, last_price)

    ranking_num = weighted_change_63 + change_126 + change_189 + change_252


    return ranking_num


def advance_decline_line_data():
    """
    Website Source:
        https://www.wsj.com/market-data/stocks/marketsdiary

    From Website:
        *Primary market NYSE, NYSE American or NYSE Arca only. †Compares the ratio of advancing to declining issues
        with the ratio of volume of shares rising and falling. Arms Index or
        TRIN = (advancing issues / declining issues) /
        (composite volume of advancing issues / composite volume of declining issues).

        Generally, an Arms of less than 1.00 indicates buying demand; above 1.00 indicates selling pressure.
        Sources: FactSet, Dow Jones Market Data
    :return:
    """

    op_dict = {"websiteTimeStamps": {}}

    diary_url_one = 'https://www.wsj.com/market-data/stocks/marketsdiary?id=%7B%22application%22%3A%22WSJ%22%2C%22' \
                    'marketsDiaryType%22%3A%22weeklyTotals%22%7D&type=mdc_marketsdiary'

    diary_url_two = 'https://www.wsj.com/market-data/stocks/marketsdiary?id=%7B%22application' \
                    '%22%3A%22WSJ%22%2C%22marketsDiaryType%22%3A%22diaries%22%7D&type=mdc_marketsdiary'

    diary_url_three = 'https://www.wsj.com/market-data/stocks/marketsdiary?id=%7B%22application' \
                      '%22%3A%22WSJ%22%2C%22marketsDiaryType%22%3A%22breakdownOfVolumes%22%7D&type=mdc_marketsdiary'

    weekly_totals = rC.use_requests_return_json(diary_url_one, add_user_agent="yes")
    weekly_timestamp = weekly_totals["data"]["timestamp"]
    for index in weekly_totals["data"]["indexes"]:
        index_key = index["id"].lower()
        op_dict.update({index_key: {}})
        op_dict[index_key].update({"weekly": index["weeklyTotals"]})

    tC.sleep(0.5)

    diaries = rC.use_requests_return_json(diary_url_two, add_user_agent="yes")
    daily_timestamp = diaries["data"]["timestamp"]
    for exchange_data in diaries['data']['instrumentSets']:
        exchange = exchange_data["headerFields"][0]['label'].replace(" ", "").lower()
        data = exchange_data["instruments"]
        op_dict[exchange].update({"daily": data.copy()})

    tC.sleep(0.5)
    daily_volumes = rC.use_requests_return_json(diary_url_three, add_user_agent="yes")
    volume_timestamp = daily_volumes["data"]["timestamp"]
    op_dict["nyse"].update({"volume": daily_volumes['data']['instruments']})

    op_dict["websiteTimeStamps"].update(
        {"daily": daily_timestamp, "weekly": weekly_timestamp, "volume": volume_timestamp})

    return op_dict


if __name__ == '__main__':
    print("yahoo: ", ibd_relative_strength("uber", data_source="yahoo"))
    # print("td: ", ibd_relative_strength("amal", data_source="tda"))
    stop = 1
