from lukhed_stocks.cat import CatWrapper
from lukhed_stocks.wikipedia import WikipediaStocks

# A bunch of functions to retrieve ticker lists without an API

########################
# Exchange functions
########################
def get_nasdaq_stocks(tickers_only=False, data_source='cat'):
    """
    The Nasdaq Stock Market is a global electronic marketplace known for its high concentration of 
    technology and growth-oriented companies.

    Parameters
    ----------
    tickers_only : bool, optional
        If True, will only return a list of strings that are the stock tickers, by default False
    data_source : str, optional
        Change the source of data to use, by default 'cat': https://catnmsplan.com/reference-data

        Current options are: 'cat'

    Returns
    -------
    list()
        List of stocks listed on the exchange per the given source.
    """

    cw = CatWrapper()
    data = cw.get_cat_reported_equities(exchange_code_filter='Q')

    if tickers_only and data_source.lower() == 'cat':
        data = [x['ticker'] for x in data if not x['testIssueFlag'] and not x['dataError']]

    return data

def get_nyse_stocks(tickers_only=False, data_source='cat'):
    """
    The New York Stock Exchange (NYSE) is one of the world's largest and most well-known stock exchanges, 
    hosting many of the biggest and most established companies.

    Parameters
    ----------
    tickers_only : bool, optional
        If True, will only return a list of strings that are the stock tickers, by default False
    data_source : str, optional
        Change the source of data to use, by default 'cat': https://catnmsplan.com/reference-data

        Current options are: 'cat'

    Returns
    -------
    list()
        List of stocks listed on the exchange per the given source.
    """

    cw = CatWrapper()
    data = cw.get_cat_reported_equities(exchange_code_filter='N')

    if tickers_only and data_source.lower() == 'cat':
        data = [x['ticker'] for x in data if not x['testIssueFlag'] and not x['dataError']]

    return data

def get_otc_stocks(tickers_only=False, data_source='cat'):
    """
    Over-The-Counter (OTC) equities are securities that trade outside of formal exchanges like the NYSE or Nasdaq. 
    These trades occur directly between parties, often facilitated by broker-dealers, and include companies 
    not listed on major exchanges.

    Parameters
    ----------
    tickers_only : bool, optional
        If True, will only return a list of strings that are the stock tickers, by default False
    data_source : str, optional
        Change the source of data to use, by default 'cat': https://catnmsplan.com/reference-data

        Current options are: 'cat'

    Returns
    -------
    list()
        List of stocks listed on the exchange per the given source.
    """

    cw = CatWrapper()
    data = cw.get_cat_reported_equities(exchange_code_filter='U')

    if tickers_only and data_source.lower() == 'cat':
        data = [x['ticker'] for x in data if not x['testIssueFlag'] and not x['dataError']]

    return data

def get_iex_stocks(tickers_only=False, data_source='cat'):
    """
    The Investors Exchange (IEX) is a U.S. stock exchange known for its focus on fairness and transparency in 
    trading, aiming to protect investors from predatory trading practices.

    Parameters
    ----------
    tickers_only : bool, optional
        If True, will only return a list of strings that are the stock tickers, by default False
    data_source : str, optional
        Change the source of data to use, by default 'cat': https://catnmsplan.com/reference-data

        Current options are: 'cat'

    Returns
    -------
    list()
        List of stocks listed on the exchange per the given source.
    """

    cw = CatWrapper()
    data = cw.get_cat_reported_equities(exchange_code_filter='V')

    if tickers_only and data_source.lower() == 'cat':
        data = [x['ticker'] for x in data if not x['testIssueFlag'] and not x['dataError']]

    return data


########################
# Index functions
########################
def get_sp500_stocks(tickers_only=False, data_source='wikipedia'):
    """
    the S&P 500 tracks the performance of 500 of the largest publicly traded companies in the 
    United States. This index is widely regarded as a key indicator of the overall health of the U.S. stock market 
    and economy.

    Parameters
    ----------
    tickers_only : bool, optional
        If True, will only return a list of strings that are the stock tickers, by default False
    data_source : str, optional
        Change the source of data to use, by default 'wikipedia': 
        https://en.wikipedia.org/wiki/List_of_S%26P_500_companies

        Current options are: 'wikipedia'

    Returns
    -------
    list()
        List of stocks listed on the exchange per the given source.
    """

    wiki = WikipediaStocks()
    data = wiki.get_sp500_data()

    if tickers_only and data_source.lower() == 'wikipedia':
        data = [x['Symbol'] for x in data]
    
    return data



