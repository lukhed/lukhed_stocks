from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC
import csv


class AlphaVantage:
    """
    https://www.alphavantage.co/documentation/

    We are pleased to provide free stock API service for our global community of users for up to
    5 API requests per minute
    and
    500 requests per day. If you would like to target a larger API call volume, please visit premium membership.

    """
    def __init__(self):
        self.b_url = "https://www.alphavantage.co/query?function="
        self.key_string = "&apikey=" + fC.read_single_line_from_file(osC.create_file_path_string(
            ["resources", "commonStocks", "keys", "alpha_vantage_key.txt"]))
        self.api = None

    def get_quote(self, ticker):
        """
        Example: https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=demo

        :param ticker:
        :return: dict(), with ticker info
        """
        ep = self._create_endpoint("GLOBAL_QUOTE", symbol=ticker)

        return rC.use_requests_return_json(ep)

    def get_company_overview(self, ticker):
        ep = self._create_endpoint("OVERVIEW", symbol=ticker)

        return rC.use_requests_return_json(ep)

    def _create_endpoint(self, function, symbol=None, interval=None, time_period=None, series_type=None,
                         maturity=None):
        ep = self.b_url + function

        if symbol is not None:
            ep = ep + "&symbol=" + str(symbol)
        if interval is not None:
            ep = ep + "&interval=" + str(interval)
        if time_period is not None:
            ep = ep + "&time_period=" + str(time_period)
        if series_type is not None:
            ep = ep + "&series_type=" + str(series_type)
        if maturity is not None:
            ep = ep + "&maturity=" + str(maturity)

        return ep + self.key_string

    def get_sma(self, ticker, sma_int, interval="daily", series_type="close"):
        """
        Example: https://www.alphavantage.co/query?function=SMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo

        :param ticker: str(), ticker you are interested
        :param sma_int: int() or str(), the SMA you are interested in, for example 50, 100, or 200.
        :param interval:
        :param series_type:
        :return:
        """

        f = "SMA"
        ep = self._create_endpoint(f, symbol=ticker, interval=interval, time_period=sma_int, series_type=series_type)

        return rC.use_requests_return_json(ep)

    def get_reported_annual_inflation(self):
        """
        Example: 'https://www.alphavantage.co/query?function=SMA&symbol=NEM&interval=daily&time_period=50&series_type=close&apikey=P8ZA0NFAOF8UZCGY'

        :return: dict(), annual inflation numbers
        """

        ep = self._create_endpoint("INFLATION")

        return rC.use_requests_return_json(ep)

    def get_monthly_expected_inflation(self):
        """
        Data is delayed, useless

        Example: 'https://www.alphavantage.co/query?function=INFLATION_EXPECTATION&apikey=demo'

        :return:
        """

        ep = self._create_endpoint("INFLATION_EXPECTATION")
        return rC.use_requests_return_json(ep)

    def get_cpi(self, interval="monthly"):
        """
        The Consumer Price Index (CPI) is a measure of the average change over time in the prices paid by urban
        consumers for a market basket of consumer goods and services. Indexes are available for the U.S.
        and various geographic areas. Average price data for select utility, automotive fuel, and food
        items are also available.
        CPI info: https://www.bls.gov/cpi/#:~:text=February%202022%20CPI%20data%20are,Eastern%20Time.

        Example: https://www.alphavantage.co/query?function=CPI&interval=monthly&apikey=demo

        :param interval: str(), "monthly" or "semiannual"
        :return:
        """

        ep = self._create_endpoint("CPI", interval=interval)

        return rC.use_requests_return_json(ep)

    def get_consumer_sentiment(self):
        """
        Data is delayed by 1 month, useless doing historical studies

        Example: https://www.alphavantage.co/query?function=CONSUMER_SENTIMENT&apikey=demo

        :return: list() of dicts()
        """

        ep = self._create_endpoint("CONSUMER_SENTIMENT")

        return rC.use_requests_return_json(ep)

    def get_federal_funds_rate(self, interval="monthly"):
        """

        example: https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=monthly&apikey=demo

        :param interval: str(), daily, weekly, monthly
        :return:
        """

        ep = self._create_endpoint("FEDERAL_FUNDS_RATE", interval=interval)

        return rC.use_requests_return_json(ep)

    def get_treasury_yield(self, interval="daily", maturity="10year"):
        """

        example: https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=monthly&maturity=10year&apikey=demo

        :param interval: str(), daily, weekly, monthly
        :param maturity: str(), 3month, 5year, 10year, 30year
        :return:
        """

        ep = self._create_endpoint("TREASURY_YIELD", interval=interval, maturity=maturity)
        return rC.use_requests_return_json(ep)

    def get_retail_sails(self):
        """
        The data hits the news wires at 8:30 Eastern Time on or around the 13th of every month.

        example: https://www.alphavantage.co/query?function=RETAIL_SALES&apikey=demo

        :return: dict(), retail sales
        """

        ep = self._create_endpoint("RETAIL_SALES")
        return rC.use_requests_return_json(ep)

    def get_durable_good_orders(self):
        """
        Released at the end of the month for the prior month.

        example: https://www.alphavantage.co/query?function=DURABLES&apikey=demo

        :return:
        """

        ep = self._create_endpoint("DURABLES")
        return rC.use_requests_return_json(ep)

    def get_unemployment_rate(self):
        """

        example: https://www.alphavantage.co/query?function=UNEMPLOYMENT&apikey=demo
        source: https://fred.stlouisfed.org/series/UNRATE

        :return:
        """

        ep = self._create_endpoint("UNEMPLOYMENT")
        return rC.use_requests_return_json(ep)

    def get_payroll(self):
        """
        montly report

        example: https://www.alphavantage.co/query?function=NONFARM_PAYROLL&apikey=demo

        :return:
        """

        ep = self._create_endpoint("NONFARM_PAYROLL")
        return rC.use_requests_return_json(ep)

    def get_ipo_calendar(self):
        """
        This endpoint uses csv, return is a list

        example: https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey=demo


        :return: list()
        """

        ep = self._create_endpoint("IPO_CALENDAR")
        response = rC.requests_get_url_content(ep)
        csv_content = response.decode('utf-8')

        return list(csv.reader(csv_content.splitlines(), delimiter=','))

    def is_trading_open_now(self, region='United States'):
        """
        Returns the status of the market now

        example: https://www.alphavantage.co/query?function=MARKET_STATUS&apikey=demo

        :return:
        """

        ep = self._create_endpoint("MARKET_STATUS")
        response = rC.basic_request(ep)
        parsed_response = response.json()

        current_status = [x for x in parsed_response['markets'] if x['region'] == region][0]['current_status']

        if current_status == 'closed':
            return False
        elif current_status == 'open':
            return True
        else:
            return 'error'


def _class_testing():
    ava = AlphaVantage()
    ava.get_ipo_calendar()
    # test = ava.get_sma("SPY", 50)
    # test = ava.get_reported_annual_inflation()
    # test = ava.get_cpi()
    # test = ava.get_quote("GRN")
    # test = ava.get_treasury_yield()
    # test = ava.get_retail_sails()
    # test = ava.get_durable_good_orders()
    # test = ava.get_unemployment_rate()
    # test = ava.get_payroll()


if __name__ == '__main__':
    av = AlphaVantage()
    quote = av.get_company_overview("CRWD")
    test = av.is_trading_open_now()
    test = av.get_ipo_calendar()
    stop = 1
