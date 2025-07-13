from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC

class Robinhood:
    def __init__(self, random_user_agent=True, api_delay=0.5):
        self.add_user_agent = random_user_agent
        self.api_delay = api_delay  # Delay in seconds between API calls
        pass

    def _unauthenticated_call(self, url, method="GET", params=None):
        """
        Make an unauthenticated API call to the specified URL.

        Parameters
        ----------
        url : _type_
            _description_
        method : str, optional
            The HTTP method to use for the request, by default "GET"
        params : _type_, optional
            Query parameters for the request, by default None

        Returns
        -------
        _type_
            The JSON response from the API or an error message
        """
        r = rC.request_json(
            url=url,
            method=method,
            params=params,
            add_user_agent=self.add_user_agent
        )
        if self.api_delay:
            tC.sleep(self.api_delay)

        return r

    def get_all_instruments(self, retrieve_all=False):
        """
        By default, returns a paginated list of all instruments tracked by Robinhood. Note: not all are trade-able.

        If retrieve_all is True, it will return all instruments in a single list.

        Parameters
        ----------
        retrieve_all : bool, optional
            If True, will complete full retrieval by pagination, by default False.
            Note: this can take a long time as there are ~270 pages as of 7/25. It is recommended to ensure the api
            delay is on when using this option (set upon class instantiation).

        Returns
        -------
        list
            A list of instruments, each represented as a dictionary containing details about the instrument.
        """
        url = 'https://api.robinhood.com/instruments/'
        
        instrument_list = []
        complete = False
        page_url = url
        page_count = 1
        while not complete:
            print(f"Retrieving page {page_count} of instruments...")
            r = self._unauthenticated_call(page_url, method="GET")
            page_count += 1
            
            try:
                instrument_list.extend(r['results'].copy())
            except KeyError:
                print("No results found in the response.")

            if not retrieve_all:
                complete = True
            else:
                page_url = r['next']
                if not page_url:
                    complete = True

        return instrument_list
    
    def get_instrument_data_by_symbol(self, symbol):
        """
        Retrieve instrument data by its symbol.

        Parameters
        ----------
        symbol : str
            The stock symbol of the instrument.

        Returns
        -------
        dict
            A dictionary containing the instrument data if found, otherwise None.
        """
        url = f'https://api.robinhood.com/instruments/?symbol={symbol}'
        r = self._unauthenticated_call(url, method="GET")
        
        if 'results' in r and r['results']:
            return r['results'][0]
        
        return None
    
    def search_instruments_by_symbol_keyword(self, keyword):
        """
        Search for instruments by a keyword in their symbol.

        Parameters
        ----------
        keyword : str
            The keyword to search for in the instrument symbols.

        Returns
        -------
        list
            A list of instruments that match the keyword.
        """
        url = f'https://api.robinhood.com/instruments/?query={keyword}'
        r = self._unauthenticated_call(url, method="GET")
        
        if 'results' in r:
            return r['results']
        
        return []
    
    def _not_working_general_search(self, search_query):
        """
        NOT WORKING: NEEDS AUTH?
        Search for instruments by a keyword in their name or symbol.

        Parameters
        ----------
        keyword : str
            The keyword to search for in the instrument names or symbols.

        Returns
        -------
        list
            A list of instruments that match the keyword.
        """
        url = "https://bonfire.robinhood.com/search/"
        params = {
            "content_types": "instruments,lists,currency_pairs,education,deeplinks,active_futures,non_active_futures,market_indexes",
            "query": search_query,
            "query_context": "default",
            "user_origin": "US"
        }

        r = self._unauthenticated_call(url, method="GET", params=params)

        if 'results' in r:
            return r['results']
        
        return []
    
    def get_most_popular_instruments(self, top_x=10, url_only=False):
        """
        Retrieve a list of the most popular instruments.

        Parameters
        ----------
        top_x : int
            The number of top instruments to retrieve. 1 to 100. Default is 10 (top 10 is returned).
        url_only : bool
            If True, only the URLs of the instruments will be returned. Default is False.

        Returns
        -------
        list
            A list of the most popular instruments, each represented as a dictionary.
            If url_only is True, returns a list of URLs to the instrument details instead.
        """
        url = "https://api.robinhood.com/midlands/tags/tag/100-most-popular/"
        r = self._unauthenticated_call(url, method="GET")
        
        if 'instruments' in r:
            top_100_results = r['instruments']
        else:
            top_100_results = []

        if url_only:
            return top_100_results[:top_x]

        x = 0
        results = []
        while x < top_x:
            results.append(
                self._unauthenticated_call(
                    url=top_100_results[x],
                    method="GET"
                )
            )
            x += 1
        
        return results