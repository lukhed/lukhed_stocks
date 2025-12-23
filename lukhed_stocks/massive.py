from massive import RESTClient
from lukhed_basic_utils.classCommon import LukhedAuth
from lukhed_basic_utils import timeCommon as tC

class Massive(LukhedAuth):
    def __init__(self, key_management='github', auth_data=None):
        
        if auth_data is None:
            # Use LukhedAuth to handle key management and retrieval
            super().__init__('massive', key_management=key_management)
            if self._auth_data is None:
                self._auth_setup()
        else:
            # Directly use provided auth_data
            self._auth_data = auth_data

        self.api_key = self._auth_data['key']
        self.client = RESTClient(api_key=self.api_key)
        stop = 1

    def _auth_setup(self):
        """
        Set up massive authentication.

        Parameters
        ----------
        None
        """
        if self._auth_data is None:
            # Walk the user through the basic auth setup
            input("Massive (previously Polygon.io) requires an API key (https://massive.com/docs/rest/quickstart). " \
            "You will be asked to paste your key in the next step. It will be stored for future use based on your  " \
            "instantiation parameters (stored on local machine or your private github). Press enter to start.")
            key = input("Enter key: ")

            self._auth_data = {
                "key": key
            }
            
            # Write auth data to user specified storage
            self.kM.force_update_key_data(self._auth_data)
            print("Basic auth data has been set up successfully.")

    def get_indice_list(self, free_tier_limits=True):
        tickers = []
        page_count = 0
        for resp in self.client.list_tickers(market="indices", 
                                                active="true", 
                                                order="asc", 
                                                limit="1000", 
                                                sort="last_updated_utc"):
            tickers.append(resp)
            page_count += 1
            if page_count == 999 and free_tier_limits:
                page_count = 0
                print("Sleeping between pages")
                tC.sleep(12.5)

        return [{"name": x.name, "ticker": x.ticker, "locale": x.locale, "active": x.active} for x in tickers]
        stop = 1

    def get_indice_snapshot(self, custom_index_list=None):
        """
        Get stock indice data for major indices.

        https://massive.com/docs/rest/indices/snapshots/indices-snapshot

        Parameters
        ----------
        custom_index_list : list, optional
            Custome list of indices, by default None

        Returns
        -------
        Massive API response, see https://polygon.io/docs/stocks/get_v1_last_quote_stocks__indiceSymbol_
            _description_
        """

        major_indices = (["I:SPX", "I:DJI", "I:VIX", "I:COMP", "I:RUT", "I:NYSE"] 
                         if custom_index_list is None 
                         else custom_index_list)
        snapshot = [x for x in self.client.get_snapshot_indices(major_indices)]
        return snapshot
    
    def get_market_holidays(self):
        """
        Get upcoming market holidays.

        https://massive.com/docs/rest/marketstatus/upcoming-holidays

        Parameters
        ----------
        None

        Returns
        -------
        Massive API response, see https://massive.com/docs/rest/marketstatus/upcoming-holidays
        """

        holidays = [x for x in self.client.get_market_holidays()]
        j = [{"close": x.close, 
              "date": x.date, 
              "exchange": x.exchange, 
              "name": x.name, 
              "open": x.open, 
              "status": x.status} for x in holidays]
        return j