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

    def _get_id_for_symbol(self, symbol):
        """
        Retrieve the ID for a given stock symbol.

        Parameters
        ----------
        symbol : str
            The stock symbol to retrieve the ID for.

        Returns
        -------
        str
            The ID of the instrument if found, otherwise None.
        """
        data = self.get_basic_data(symbol)
        if data and 'id' in data:
            return data['id']
        
        return None
    
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
    
    
    def _parse_symbol_input(self, symbols):
        """
        Parse the input symbols to ensure they are in a list format.

        Parameters
        ----------
        symbols : str, list
            The stock symbol(s) to be parsed.

        Returns
        -------
        list
            A list of symbols.
        """
        if isinstance(symbols, str):
            return [symbols]
        elif isinstance(symbols, list):
            return symbols
        else:
            raise ValueError("Symbols must be a string or a list of strings.")
        
    ###################
    # Get data by symbol(s)
    ###################
    def get_basic_data(self, symbol):
        """
        Retrieve instrument data by its symbol.

        Parameters
        ----------
        symbol : str or list
            The stock symbol of the instrument or a list of symbols.

        Returns
        -------
        dict
            A dictionary containing the instrument data if found, otherwise None.
        """
        symbol_list = self._parse_symbol_input(symbol)

        url = f'https://api.robinhood.com/instruments/?symbols='
        url += ','.join(symbol_list)

        r = self._unauthenticated_call(url, method="GET")
        
        try:
            results = r['results']
        except KeyError:
            results = []

        if isinstance(symbol, list):
            for i, s in enumerate(symbol):
                results[i] = {'symbol': s, **results[i]}
        else:
            results = results[0] if results else None

        return results
    
    def get_fundamentals(self, symbol):
        """
        Retrieve fundamental data for an instrument by its symbol.

        Parameters
        ----------
        symbol : str, list
            The stock symbol of the instrument or a list of symbols.

        Returns
        -------
        dict
            A dictionary containing the fundamental data if found, otherwise None.
        """
        symbol_list = self._parse_symbol_input(symbol)

        url = 'https://api.robinhood.com/fundamentals/?symbols='
        url += ','.join(symbol_list)

        r = self._unauthenticated_call(url, method="GET")
        
        try:
            results = r['results']
        except KeyError:
            results = []

        if isinstance(symbol, list):
            for i, s in enumerate(symbol):
                results[i] = {'symbol': s, **results[i]}

        
        return results
    
    def get_basic_chart_data(self, symbol, span='all', extended_hours=False):
        """
        Retrieves the data related to the basic price chart shown on robinhood.com for a given instrument.

        Parameters
        ----------
        symbol : str
            The stock symbol of the instrument for which to retrieve historical data.
        span : str, optional
            The time span for the historical data, by default 'all'. Options include: 
            'day', 'week', 'month', '3month', 'ytd', 'year', '5year', 'all'.
        extended_hours : bool, optional
            Whether to include extended hours data, by default False.

        Returns
        -------
        list
            A list of historical price data points.
        """
        
        
        id = self._get_id_for_symbol(symbol)
        url = f'https://bonfire.robinhood.com/instruments/{id}/historical-chart/?display_span={span}&hide_extended_hours={"true" if not extended_hours else "false"}'
        r = self._unauthenticated_call(url, method="GET")

        lines = r['chart_data']['chart']['lines']
        segments = lines[len(lines) - 1]['segments']
        
        points = []
        for segment in segments:
            points.extend(segment['points'])

        results = []
        for point in points:
            price = point['cursor_data']['primary_value']['value']
            date = point['cursor_data']['label']['value'].replace("LISTED ON ", "")
            relative_gain = point['cursor_data']['secondary_value']['main']['value']

            results.append({
                'price': price,
                'date': date,
                'relative_gain': relative_gain
            })

        return results

    ###################
    # Lists
    ###################
    def get_most_held_instruments(self, top_x=100, return_symbols_only=False):
        """
        Retrieves the top 100 most popular instruments list which is defined by robinhood:
        'By popular demand. See which stocks and ETFs are most commonly held by Robinhood customers.'.

        Parameters
        ----------
        top_x : int
            The number of top instruments to retrieve. 1 to 100. Default is 100.
        return_symbols_only : bool
            If True, only the symbols of the instruments will be returned. Default is False.

        Returns
        -------
        list
            A list of the most popular instruments, each represented as a dictionary.
            If return_symbols_only is True, returns a list of symbols of the instruments instead.
        """
        url = "https://api.robinhood.com/midlands/tags/tag/100-most-popular/"
        r = self._unauthenticated_call(url, method="GET")
        
        if 'instruments' in r:
            top_100_results = r['instruments']
        else:
            top_100_results = []

        if top_x > 75:
            url1 = [x.split('/')[-2] for x in top_100_results[:74]]
            url2 = [x.split('/')[-2] for x in top_100_results[74:]]
            res1 = self._unauthenticated_call(
                'https://api.robinhood.com/instruments/?ids=' + '%2C'.join(url1),
                method="GET"
            )
            res2 = self._unauthenticated_call(
                'https://api.robinhood.com/instruments/?ids=' + '%2C'.join(url2),
                method="GET"
            )
            try:
                results = res1['results'] + res2['results']
            except KeyError:
                results = [ ]
        else:
            ids = [x.split('/')[-2] for x in top_100_results]
            url = 'https://api.robinhood.com/instruments/?ids=' + '%2C'.join(ids[:top_x])
            results = self._unauthenticated_call(url, method="GET")
            try:
                results = results['results']
            except KeyError:
                results = []

        if return_symbols_only:
            results = [x['symbol'] for x in results]
        
        return results

    ###################
    # Search
    ###################
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
    
    
    
    