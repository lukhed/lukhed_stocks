from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from typing import Optional
from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.requests import StockQuotesRequest
from alpaca.data.requests import StockSnapshotRequest


class AlpacaMarketData:
    """
    To setup a new key:
    https://alpaca.markets/docs/market-data/getting-started/

    Documentation:
    https://github.com/alpacahq/alpaca-py
    https://alpaca.markets/docs/python-sdk/market_data.html
    https://alpaca.markets/docs/python-sdk/api_reference/data_api.html

    There are 2 historical data clients: StockHistoricalDataClient and CryptoHistoricalDataClient
    from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient

    key
    PKZXB3K9Z685JL1RNUH4

    secret
    iURanGzZdMB6Wy4NMIlQwL2EjzRQHB9j6EhxGQ5l
    """

    def __init__(self):
        stop = 1
        self.stock_api = None                       # type: Optional[StockHistoricalDataClient]
        self.crypto_api = None                      # type: Optional[CryptoHistoricalDataClient]

    def _check_create_stock_quote_api(self):
        if self.stock_api is None:
            self.stock_api = StockHistoricalDataClient("PKZXB3K9Z685JL1RNUH4",  "iURanGzZdMB6Wy4NMIlQwL2EjzRQHB9j6EhxGQ5l")

    def get_latest_quote(self, ticker):
        self._check_create_stock_quote_api()
        req_obj = StockLatestQuoteRequest(symbol_or_symbols=ticker)
        quote = self.stock_api.get_stock_latest_quote(req_obj)
        stop = 1

    def get_stock_snapshot(self, ticker):
        self._check_create_stock_quote_api()
        req_ob = StockSnapshotRequest(symbol_or_symbols=ticker)
        snapshot = self.stock_api.get_stock_snapshot(req_ob)
        stop = 1


def main():
    apd = AlpacaMarketData()
    apd.get_stock_snapshot("CRWD")


if __name__ == '__main__':
    main()
