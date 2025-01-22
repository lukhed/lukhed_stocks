from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC
from resources.aceCommon import timeCommon as tC


class PolygonIo:
    """
    https://polygon.io/docs/stocks/getting-started

    We are pleased to provide free stock API service for our global community of users for up to
    5 API requests per minute
    and
    500 requests per day. If you would like to target a larger API call volume, please visit premium membership.

    """
    def __init__(self, use_api_delay=True):

        # API Rate Management variables
        if use_api_delay:
            self.api_delay = 1
        else:
            self.api_delay = 0
        self._call_counter = 0

        # Time variables
        self.day = tC.get_current_day()
        self.date = tC.get_date_today(return_string=True)

        self.resource_dir = osC.create_file_path_string(['resources', 'commonStocks'])
        self._base_url = 'https://api.polygon.io/'
        self._api_key = fC.read_single_line_from_file(
            osC.append_to_dir(self.resource_dir, ['keys', 'polygon_key.txt'], list=True)
        )


    def _create_url(self, version_int, end_point_list):
        """
        Used by all functions to  construct the proper URL

        :param version_int:         int(), for example, 1 ends up with 'v1' in the url

        :param end_point_list:      list(), list of the endpoint sub dirs. For example, if the api is
                                    /v1/marketstatus/now, the end_point_list is [marketstatus, now]

        :return:                    str(), url to make the call to the specified endpoint
        """

        base = self._base_url + 'v' + str(version_int) + "/"
        for sub_end in end_point_list:
            base = base + sub_end + "/"
        url = base[:-1] + "?apiKey=" + self._api_key

        return url

    def _make_api_call(self, url):
        """
        Use this method to make an API call so as to properly use delays

        :param url:
        :return:
        """

        if self._call_counter == 0:
            pass
        else:
            tC.sleep(self.api_delay)

        r = rC.basic_request(url)
        self._call_counter = self._call_counter + 1

        return r

    def get_market_status_now(self):
        """
        Get the current trading status of the exchanges and overall financial markets.

        https://polygon.io/docs/stocks/get_v1_marketstatus_now

        :return:    dict(), see documentation link
        """

        url = self._create_url(1, ['marketstatus', 'now'])
        r = self._make_api_call(url)
        parsed_r = r.json()

        return parsed_r

    def get_upcoming_market_holidays(self):
        """
        Get upcoming market holidays and their open/close times.

        https://polygon.io/docs/stocks/get_v1_marketstatus_upcoming

        :return:
        """

        url = self._create_url(1, ['marketstatus', 'upcoming'])
        r = self._make_api_call(url)
        parsed_r = r.json()

        return parsed_r

    def calculated_is_today_a_market_open_day(self):
        """
        This function uses logic to determine if the market is/was open today. It will potentially use the
        get_upcoming_market_holidays methods.

        :return:    bool(), True is market is open for the day, False if not
        """

        if self.day == "Saturday" or self.day == "Sunday":
            return False
        else:
            hols = self.get_upcoming_market_holidays()
            # For simplicity, we will check the nasdaq and only fully closed days (note there are "early-close" days
            n_hols = [x for x in hols if x['exchange'] == "NASDAQ" and
                                         x['status'] == 'closed' and
                                         x['date'] == self.date]

            if len(n_hols) > 0:
                return False
            else:
                return True







def testing():
    pi = PolygonIo()
    print(pi.calculated_is_today_a_market_open_day())


if __name__ == '__main__':
    testing()
