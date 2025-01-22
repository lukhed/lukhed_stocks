from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from typing import Optional
import commonStocksPolygon


def is_trading_day():
    """
    Polygon API is the current method to decide this. 5 Calls per minute. 500 per day free.

    :return:
    """
    pi = commonStocksPolygon.PolygonIo()
    trading_day = pi.calculated_is_today_a_market_open_day()
    return trading_day


def main():
    test = is_trading_day()
    stop = 1


if __name__ == '__main__':
    main()
