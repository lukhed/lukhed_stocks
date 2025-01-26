from lukhed_basic_utils import requestsCommon as rC


class WikipediaStocks:
    def __init__(self):
        # API Info
        self._header = {'User-Agent': 'lukhed_stocks (https://github.com/lukhed/lukhed_stocks)'}
        self._main_url = "https://en.wikipedia.org/w/api.php"
    
    def get_sp500_data(self):
        """
        Returns data for all the S&P 500 component stocks as listed here:
        https://en.wikipedia.org/wiki/List_of_S%26P_500_companies

        Returns
        -------
        list()
            List of dictionaries. Each list item corresponds to a row in the table at the wikipeida page.

        Example:

        {
        'Symbol': 'MMM', 
        'Security': '3M', 
        'GICS Sector': 
        'Industrials', 
        'GICS Sub-Industry': 
        'Industrial Conglomerates', 
        'Headquarters Location': 'Saint Paul, Minnesota', 
        'Date added': '1957-03-04', 
        'CIK': '0000066740', 
        'Founded': '1902
        }
        
        """
        # Parameters for the API request
        params = {
            "action": "parse",
            "page": "List of S&P 500 companies",
            "format": "json",
            "prop": "text"
        }

        response = rC.make_request(self._main_url, params=params, headers=self._header)
        data = response.json()

        # Extract table from HTML content
        html_content = data['parse']['text']['*']
        soup = rC.get_soup_from_html_content(html_content)
        table = soup.find(id='constituents')
        
        # Prase Table
        output_data = []

        columns = [x.text.strip() for x in table.findAll('th')]
        for row in table.findAll('tr')[1:]:
            temp_dict = {}
            for i, column in enumerate(columns):
                temp_dict[column] = row.findAll('td')[i].text.strip()

            output_data.append(temp_dict.copy())

        return output_data
    
    def get_djia_data(self):
        """
        Returns data for all the down jones industrial average (DJIA) as listed here:
        https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average

        Returns
        -------
        list()
            List of dictionaries. Each list item corresponds to a row in the table at the wikipeida page.

        Example:
        {
            'Company': 'Walmart', 
            'Exchange': 'NYSE', 
            'Symbol': 'WMT', 
            'Industry': 'Retailing', 
            'Date added': '1997-03-17', 
            'Notes': '', 
            'Index weighting': '1.31%'
        }
        
        """
        # Parameters for the API request
        params = {
            "action": "parse",
            "page": "Dow Jones Industrial Average",
            "format": "json",
            "prop": "text"
        }

        response = rC.make_request(self._main_url, params=params, headers=self._header)
        data = response.json()

        # Extract table from HTML content
        html_content = data['parse']['text']['*']
        soup = rC.get_soup_from_html_content(html_content)
        table = soup.find(id='constituents')
        
        # Prase Table
        output_data = []

        columns = [x.text.strip() for x in table.findAll('th', scope='col')]
        for row in table.findAll('tr')[1:]:
            temp_dict = {}
            for i, column in enumerate(columns):
                temp_dict[column] = row.findAll(['th', 'td'])[i].text.strip()

            output_data.append(temp_dict.copy())

        return output_data