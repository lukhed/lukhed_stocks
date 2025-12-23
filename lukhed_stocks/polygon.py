from lukhed_basic_utils import classCommon
from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC

class PolygonIo(classCommon.LukhedAuth):
    """
    https://polygon.io/docs/stocks/getting-started

    We are pleased to provide free stock API service for our global community of users for up to
    5 API requests per minute
    and
    500 requests per day. If you would like to target a larger API call volume, please visit premium membership.
    """

    def __init__(self, api_delay=1, key_management='github', auth_dict=None):
        """
        Initializes the SqlHelper class for managing SQL database connections and operations.

        Parameters
        ----------
        api_delay : int, optional
            Delay in seconds between API calls to avoid rate limiting, by default 1 second
        key_management : str, optional
            Options for storing your authentication data. 'local' to store your auth on your local hardware. 
            'github' to store in your private github repository (you will need a github account and github token).
            , by default 'github'
        auth_dict : dict, optional
            By default, this class will walk you through providing your authentication data to be stored according 
            to your preference via command prompts. You can also provide the necessary dictionarty via this 
            parameter to skip the setup., by default None
        """

        super().__init__('polygon', key_management=key_management)

        self._auth_dict = auth_dict
        self.api_delay = api_delay
        self._base_url = "https://api.polygon.io/"

        if self._auth_data is None:
            self._auth_setup()

        self._api_key = self._auth_data['key']
        self._call_counter = 0
        self.day = tC.get_current_day()
        self.date = tC.create_timestamp(output_format="%Y-%m-%d")

    def _auth_setup(self):
        """
        Set up polygon authentication.

        Parameters
        ----------
        None
        """
        # Walk the user through the basic auth setup
        input("Polygon requires an API key (https://polygon.io/dashboard/keys). You will be asked " \
        "to paste your key in the next step. It will be stored for future use based on your instantiation " \
        "parameters (stored on local machine or your private github). Press enter to start.")
        key = input("Enter key: ")

        self._auth_data = {
            "key": key
        }
        
        # Write auth data to user specified storage
        self.kM.force_update_key_data(self._auth_data)
        print("Authentication has been set up successfully.")

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

        r = rC.make_request(url)
        self._call_counter = self._call_counter + 1

        return r

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
    
    def is_market_open_today(self):
        """
        This function uses logic to determine if the market is/was open today. It will potentially use the
        get_upcoming_market_holidays methods.

        :return:    bool(), True is market is open for the day (including partial days), False if not
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
    