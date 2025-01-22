from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC
from resources.aceCommon import timeCommon as tC

"""
Documentation:
https://iexcloud.io/core-data-catalog

Limits:
We limit requests to 100 per second per IP measured in milliseconds, so no more than 1 request per 10 milliseconds. 
We do allow bursts, but this should be sufficient for almost all use cases. 
Note that Sandbox Testing has a request limit of 10 requests per second measured in milliseconds.

SSE endpoints are limited to 50 symbols per connection. You can make multiple connections if you 
need to consume more than 50 symbols.

Each requests costs credits. Total Monthly Credits: 50k

https://iexcloud.io/docs/api/#request-limits


API Notes:
 - Yahoo finance does not provide a great crypto offering. This api can be used to retrieve crypto prices, as the
   call costs 1 credit. Td API is currently preferred for BTC as there is no cost.
 - Since there is a credit limit here, any daily economic data needed should use AlphaVantage, as the price for
   economic indicators here is steep.
   
"""



class IEXWrapper:
    def __init__(self, sandbox=False):
        self.sandbox = sandbox
        self.key_str = _get_token_url_string(sandbox=sandbox)
        self.base_url = _get_base_url(sandbox=sandbox)

    def is_today_a_trading_day(self):
        """
        *******************:THIS NOW REQUIRES PAID ACCESS AND SANDBOX DOESN'T WORK****************************
        This function utilizes an IEX call referenced below to return information about the current day:
        /ref-data/us/dates/{type}/{direction?}/{last?}/{startDate?}

        The sandbox api actually returns the correct information, as sandbox api's with dates do.

        Credit cost: 1
        Total Monthly Credits: 50k

        :return: bool(), True if today is a trading day. False if today is not a trading day.
        """

        yes_date = tC.get_date_yesterday(return_string=True).replace("-", "")
        request_str = self.base_url + '/ref-data/us/dates/trade/next/1/' + yes_date + self.key_str
        res = rC.use_requests_return_json(request_str)

        check_date = tC.get_date_today(return_string=True)
        if check_date == res[0]["date"]:
            return True
        else:
            return False

    def get_latest_price_for_ticker(self, ticker):
        """
        This function returns the latest price for the ticker. by using the latestPrice field of quote endpoint

        More information about the timeliness of the price is here:
        https://iexcloud.zendesk.com/hc/en-us/articles/1500012488781-Real-time-and-15-minute-Delayed-Stock-Prices

        Credit cost: 1
        Total Monthly Credits: 50k
        :param: ticker: str(), ticker symbol (e.g. AAPL)
        :return: float(), price in dollars
        """

        return self._quote_end_point(ticker, "latestPrice")

    def get_latest_price_for_crypto(self, symbol):
        """
        Returns the last price available for crypto symbol.
        documentation: https://iexcloud.io/docs/api/#cryptocurrency-price
        :param symbol: str(), BTC, ETH, etc.
        :return: float(), price
        """

        if "USD" in symbol:
            pass
        else:
            symbol = symbol + "USD"

        ep = self.base_url + "/crypto/" + symbol + "/price" + self.key_str
        return float(rC.use_requests_return_json(ep)["price"])

    def _quote_end_point(self, ticker, field):
        """
        The quote endpoint returns many fields and has the option to add a field parameter to return only the
        specified field. This function will be the basis for other functions using the quote parameter.

        Available price sensitive field arguments:
        https://iexcloud.io/docs/api/#quote

        :param ticker:
        :return:
        """

        request_str = self.base_url + '/stock/' + ticker + '/quote/' + field + self.key_str
        return rC.use_requests_return_json(request_str)


def _get_base_url(sandbox=False):
    if sandbox:
        return 'https://sandbox.iexapis.com/stable'
    else:
        return 'https://cloud.iexapis.com/stable'


def _get_tokens():
    public_file = osC.create_file_path_string(['resources', 'commonStocks', 'keys', 'iex_public_key.txt'])
    secret_file = osC.create_file_path_string(['resources', 'commonStocks', 'keys', 'iex_private_key.txt'])
    sandbox_file = osC.create_file_path_string(['resources', 'commonStocks', 'keys', 'iex_sandbox_key.txt'])

    return {'public': fC.read_single_line_from_file(public_file),
            'secret': fC.read_single_line_from_file(secret_file),
            'sandbox': fC.read_single_line_from_file(sandbox_file)
    }


def _get_token_url_string(sandbox=False):
    if sandbox:
        return '?token=' + _get_tokens()['sandbox']
    else:
        return '?token=' + _get_tokens()['public']


if __name__ == '__main__':
    iex = IEXWrapper()
    print(iex.is_today_a_trading_day())
    iex = IEXWrapper()
    test = iex.get_latest_price_for_crypto("ETH")
    stop = 1