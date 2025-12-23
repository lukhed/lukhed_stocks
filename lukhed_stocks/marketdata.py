from lukhed_stocks.webull import Webull
from lukhed_stocks.robinhood import Robinhood
from lukhed_stocks.cnn import CNN
from typing import Optional

# A bunch of functions to retrieve market data (quotes, price history etc.) without an API

class MarketData:
    def __init__(self):
        self.webull = None      # type: Optional[Webull]
        self.robinhood = None   # type: Optional[Robinhood]
        self.cnn = None         # type: Optional[CNN]
    
    def _check_create_webull(self):
        if self.webull is None:
            self.webull = Webull(keep_live_cache=False, use_basics_cache=False)

    def _check_create_robinhood(self):
        if self.robinhood is None:
            self.robinhood = Robinhood()
    
    def _check_create_cnn(self):
        if self.cnn is None:
            self.cnn = CNN()
    
    def get_indice_prices(self, source='cnn'):
        """
        Get the latest prices for major indices from the specified source.

        Parameters
        ----------
        source : str, optional
            Data source, by default 'cnn'. Options: 'cnn', 'webull'

        Returns
        -------
        dict
            Latest prices for major indices

        Raises
        ------
        ValueError
            If the specified source is not supported.
        """
        source = source.lower()
        if source == 'cnn':
            self._check_create_cnn()
            return self.cnn.get_major_indices()
        elif source == 'webull':
            self._check_create_webull()
            return self.webull.get_indice_prices()
        else:
            raise ValueError("Unsupported source. Currently only 'webull' is supported.")
    
    def get_quote(self, symbol, source='webull'):
        """
        Get the latest quote for a given stock symbol or list of symbols from the specified source.

        Parameters
        ----------
        symbol : str or list
            Stock ticker symbol (e.g., 'AAPL') or a list of symbols
        source : str, optional
            Data source, by default 'webull'. Options: 'webull'

        Returns
        -------
        dict
            Latest quote data

        Raises
        ------
        ValueError
            If the specified source is not supported.
        """
        
        if source == 'webull':
            self._check_create_webull()
            return self.webull.get_quote(symbol)
        else:
            raise ValueError("Unsupported source. Currently only 'webull' is supported.")
        
    def get_price_history(self, symbol, interval='d1', points=800, source='webull'):
        """
        Get price history for a given stock symbol from the specified source.

        Parameters
        ----------
        symbol : str
            Stock ticker symbol (e.g., 'AAPL')
        interval : str, optional
            Interval for price history, by default 'd1' (daily)
        points : int, optional
            Number of data points to retrieve, by default 800
        source : str, optional
            Data source, by default 'webull'. Options: 'webull'

        Returns
        -------
        dict
            Price history data

        Raises
        ------
        ValueError
            If the specified source is not supported.
        """
        
        if source == 'webull':
            self._check_create_webull()
            return self.webull.get_price_history(symbol, interval=interval, points=points)
        else:
            raise ValueError("Unsupported source. Currently only 'webull' is supported.")
        
    def get_indice_price_history(self, indice_symbol, interval='d1', points=800, source='webull'):
        """
        Get price history for major indices from the specified source.

        Parameters
        ----------
        indice_symbol : str
            Indice symbol (e.g., 'dji', 'nasdaq', 'spx', 'rut')
        interval : str, optional
            Interval for price history, by default 'd1' (daily)
        points : int, optional
            Number of data points to retrieve, by default 800
        source : str, optional
            Data source, by default 'webull'. Options: 'webull'

        Returns
        -------
        dict
            Price history data for the indice

        Raises
        ------
        ValueError
            If the specified source is not supported.
        """
        
        if source == 'webull':
            self._check_create_webull()
            return self.webull.get_indice_price_history(indice_symbol, interval=interval, points=points)
        else:
            raise ValueError("Unsupported source. Currently only 'webull' is supported.")
        
    def get_fundamentals(self, symbol, source='robinhood'):
        """
        Get fundamental data for a given stock symbol or list of symbols from the specified source.

        Parameters
        ----------
        symbol : str or list
            Stock ticker symbol (e.g., 'AAPL') or a list of symbols
        source : str, optional
            Data source, by default 'robinhood'. Options: 'robinhood'

        Returns
        -------
        dict or list of dict
            Fundamental data

        Raises
        ------
        ValueError
            If the specified source is not supported.
        """
        
        if source == 'robinhood':
            self._check_create_robinhood()
            return self.robinhood.get_fundamentals(symbol)
        else:
            raise ValueError("Unsupported source. Currently only 'robinhood' is supported.")
        
    def get_basic_info(self, symbol, source='robinhood'):
        """
        Get basic information for a given stock symbol or list of symbols from the specified source.

        Parameters
        ----------  
        symbol : str or list
            Stock ticker symbol (e.g., 'AAPL') or a list of symbols
        source : str, optional
            Data source, by default 'robinhood'. Options: 'robinhood'

        Returns
        -------
        dict or list of dict
            Basic information data

        Raises
        ------
        ValueError
            If the specified source is not supported.
        """
        
        if source == 'robinhood':
            self._check_create_robinhood()
            return self.robinhood.get_basic_info(symbol)
        else:
            raise ValueError("Unsupported source. Currently only 'robinhood' is supported.")