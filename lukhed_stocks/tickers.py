from lukhed_stocks.cat import CatWrapper
from lukhed_stocks.wikipedia import WikipediaStocks
from lukhed_stocks.tradingview import TradingView
from lukhed_basic_utils import requestsCommon as rC

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
        Change the source of data to use, by default 'wikipedia'
        
        Current options are: 
        'wikipedia' - https://en.wikipedia.org/wiki/List_of_S%26P_500_companies

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

def get_dow_stocks(tickers_only=False, data_source='wikipedia'):
    """
    The Dow Jones Industrial Average (DJIA), often referred to as the "Dow," comprises 30 prominent publicly 
    traded companies in the United States. These companies are selected to represent a broad spectrum of the U.S. 
    economy, encompassing various industries such as technology, finance, healthcare, and consumer goods.

    Parameters
    ----------
    tickers_only : bool, optional
        If True, will only return a list of strings that are the stock tickers, by default False
    data_source : str, optional
        Change the source of data to use, by default 'wikipedia'.

        Current options are: 
            'wikipedia': https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average

    Returns
    -------
    list()
        List of stocks listed on the exchange per the given source.
    """
    wiki = WikipediaStocks()
    data = wiki.get_djia_data()

    if tickers_only and data_source.lower() == 'wikipedia':
        data = [x['Symbol'] for x in data]
    
    return data

def get_russell2000_stocks(tickers_only=False, data_source='tradingview'):
    """
    The Russell 2000 Index is a widely recognized benchmark that measures the performance of approximately 
    2,000 small-capitalization companies within the U.S. equity market. Established in 1984 by the 
    Frank Russell Company, it serves as a key indicator for investors focusing on smaller U.S. companies.

    Parameters
    ----------
    tickers_only : bool, optional
        If True, will only return a list of strings that are the stock tickers, by default False
    data_source : str, optional
        Change the source of data to use, by default 'wikipedia'.

        Current options are: 
            'tradingview': https://www.tradingview.com/screener/
                This source returns only primary listings of the Russell 2k. To get the same results as you would 
                with the tradingview screener, you must put filter "Primary Listing" = "Yes"

    Returns
    -------
    list()
        List of stocks listed on the exchange per the given source.
    """
    tv = TradingView()
    data = tv.screener_get_stocks_by_index('russel 2000')

    if tickers_only and data_source.lower() == 'tradingview':
        data = [x['name'] for x in data['data']]
    else:
        data = data['data']
    
    return data


########################
# Other Functions
########################
def get_company_logo(ticker, output_file=None, data_source='synthfinance'):
    """
    Gets logo for the company by ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol of the company.
    output_file : str, optional
        File path to save the downloaded SVG image. If None, only the image URL is returned.
    data_source : str, optional
        Data source for fetching the logo. Currently supports 'synthfinance'. Default is 'synthfinance'.

    Returns
    -------
    str
        The URL of the company logo if output_file is None.
    """

    # Validate data source
    if data_source != 'synthfinance':
        raise ValueError(f"Unsupported data_source: {data_source}. Currently, only 'synthfinance' is supported.")

    # Construct the SynthFinTech logo URL
    logo_url = f"https://logo.synthfinance.com/ticker/{ticker.upper()}"

    # If no output file is given, return the logo URL
    if output_file is not None:
        rC.download_image(logo_url, output_file)

    return logo_url
