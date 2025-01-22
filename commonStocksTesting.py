from resources.aceCommon import osCommon as oC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as reqC
import commonStocksPortfolio

# add first puchase cost


def test_get_portfolio_from_cache():
    current_port = commonStocksPortfolio.get_portfolio_from_cache('yahoo')['tickers']
    test = 1


def test_cache_portfolio():
    commonStocksPortfolio.cache_portfolio('yahoo')
    test = 1


def test_get_tickers_from_yahoo_watchlist():
    test_dict = commonStocksPortfolio.get_tickers_from_yahoo_watchlist("Track - Speculation", first_buy_data='yes')
    test = 1

def webull_test():
    ticker_lookup = 'https://quotes-gw.webullfintech.com/api/search/pc/tickers?keyword=thr&regionId=6&pageIndex=1&pageSize=20'
    test_json = reqC.use_requests_return_json(ticker_lookup)
    industry_url = 'https://quotes-gw.webullfintech.com/api/wlas/industry/IndustryList'
    quote_url = 'https://quotes-gw.webullfintech.com/api/stock/tickerRealTime/getQuote?tickerId=913254343&includeSecu=1&includeQuote=1&more=1'



if __name__ == '__main__':
    webull_test()

