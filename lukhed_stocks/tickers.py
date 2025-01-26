from lukhed_basic_utils import osCommon as osC
from lukhed_basic_utils import fileCommon as fC
from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC

# A bunch of functions to retrieve ticker lists

class CatWrapper:
    def __init__(self):
        """
        CAT = Consolidated Audit Trail
        
        https://catnmsplan.com/about-cat
        'On July 11, 2012, the U.S. Securities and Exchange Commission (SEC) voted to adopt Rule 613 under 
        Regulation NMS requiring the national securities exchanges and national securities associations 
        listed below (collectively, the SROs) to submit an NMS plan (Plan) to the SEC to create, implement, 
        and maintain a consolidated audit trail (CAT)...'


        """
        sources = None

    def get_cat_reported_equities(self, exchange_code_filter=None, equities_or_options='equities', 
                                    specify_file='eod'):
        """
        Get a list of is a comprehensive list that includes all National Market System (NMS) stocks and certain 
        over-the-counter (OTC) equity securities that are subject to reporting requirements under the 
        Consolidated Audit Trail (CAT) for a given trading day. This list is updated multiple times daily to reflect 
        any changes, ensuring that firms have the most current information for accurate reporting. 

        https://catnmsplan.com/reference-data

        
        Parameters
        ----------
        exchange_code_filter : str(), optional
            If exchange code provided, the result will be filtered for the given exchange. Primary Listing Exchange:
            A = NYSE American
            N = NYSE
            O = OTCBB
            P = NYSE ARCA
            Q = Nasdaq
            U = OTC Equity
            V = IEX
            Z = Cboe BZX
            Else NULL
        
        None by default, and all equities included.

        equities_or_options : str(), optional
            'equities' pulls stocks and 'options' pulls the options file. 'equities' by default.
            
        specify_file : str(), optional
            The file you want to pull from CAT may depend on the day and time of day you are pulling data. You have 
            three choices:
                'eod' (end of day)
                'sod' (start of day)
                'intraday'
            
            By default 'eod'

            The SOD CAT Reportable Equity Securities Symbol Master is published by 6 a.m. ET, and the EOD file 
            is published by 6 p.m. ET. The intraday file is published approximately every 2 hours beginning at 
            10:30 a.m. ET, and includes any updates made to the security master during the day, prior to the 
            EOD file posting. The EOD file contains any securities added during the transaction date. 
        """

        base_url = 'https://files.catnmsplan.com/symbol-master/'

        if equities_or_options.lower() == 'equities':
            url = base_url + 'FINRACATReportableEquitySecurities_'
        elif equities_or_options.lower() == 'options':
            url = base_url + 'CATReportableOptionsSymbolMaster_'
        else:
            print(f"ERROR: '{equities_or_options}' is an invalid equities_or_options parameter. Use 'equities' or 'options'")
            return []
        
        if specify_file.lower() in ['eod', 'sod', 'intraday']:
            url = url + specify_file.upper() + '.txt'
        else:
            print(f"ERROR: '{specify_file}' is an invalid specify_file parameter. Use 'eod', 'sod', or 'intraday'")
            return []
        
        data = rC.make_request(url)
        decoded_data = data.content.decode("utf-8")
        
        lines = decoded_data.split('\n')

        output_data = []
        for entry in lines[1:]:
            line_list = entry.split("|")

            error_flag = False

            try:
                ticker = line_list[0]
            except IndexError:
                ticker = ""
                error_flag = True

            try:
                issue_name = line_list[1]
            except IndexError:
                issue_name = ""
                error_flag = True

            try:
                listing_exchange = line_list[2]
            except IndexError:
                listing_exchange = ""
                error_flag = True

            try:
                test_issue_flag = line_list[3]
                if test_issue_flag == 'Y':
                    test_issue_flag = True
                elif test_issue_flag == 'N':
                    test_issue_flag = False
            except IndexError:
                test_issue_flag = True
                error_flag = True


            output_data.append({
                'ticker': ticker,
                'issueName': issue_name,
                'listingExchange': listing_exchange,
                'testIssueFlag': test_issue_flag,
                'fullData': line_list.copy(),
                'dataError': error_flag
            })

        if exchange_code_filter is not None:
            output_data = [x for x in output_data if x['listingExchange'].lower() == exchange_code_filter.lower()]
        
        return output_data


class WikipediaStocks:
    def __init__(self):
        stop = 1
    
    


def get_all_tickers_s_and_p(return_type="all"):
    """
    Returns a list of companies in s&p, each being a dict with ticker, security, industry, subIndustry key.
    Use return type to customize return.

    :param return_type:         str(), all, ticker, security, industry, sub industry
    :return:                    dict(), S&P ticker information
    """
    soup = rC.get_soup('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', add_user_agent=True)
    table = soup.find('table', {'class': 'wikitable sortable'})

    tickers_only = list()
    securities_only = list()
    industries_only = list()
    sub_industries_only = list()
    full_response = list()
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.strip()
        security = row.findAll('td')[1].text.strip()
        industry = row.findAll('td')[3].text.strip()
        sub_industry = row.findAll('td')[4].text.strip()

        tickers_only.append(ticker)
        securities_only.append(security)
        industries_only.append(industry)
        sub_industries_only.append(sub_industry)
        full_response.append(
            {
                "ticker": ticker,
                "security": security,
                "industry": industry,
                "subIndustry": sub_industry
            }
        )

    if "ticker" in return_type:
        return tickers_only
    elif "security" in return_type:
        return securities_only
    elif "sub industry" in return_type:
        return sub_industries_only
    elif "industry" in return_type:
        return industries_only
    else:
        return full_response


def get_all_tickers_nasdaq_exchange(use_cache=True):
    """
    Returns simple list of tickers list on nasdaq exchange

    :param use_cache: bool(), default to true as new data should only be pulled once a trading period as there is
                              dependency on a limited API to check trading hours.
    :return: list(), simple list of tickers
    """
    tickers = get_all_tickers(use_cache_only=use_cache, exchange_code="Q")
    return tickers


def get_major_indices_service_named(service, return_type='tickers'):
    # By default, returns a list of the major indices tickers for the named service
    # supported services: yahoo
    # for return_types, pass 'names' to get a list of names or 'full' to get the entire file returned as a list of list

    f_name = 'major_indices.csv'
    return _ticker_list_return(service, f_name, return_type)


def get_major_crypto_coins_service_named(service, return_type='tickers'):
    # By default, returns a list of the major crypto tickers for the named service
    # supported services: yahoo
    # for return_types, pass 'names' to get a list of names or 'full' to get the entire file returned as a list of list

    f_name = 'major_crypto.csv'
    return _ticker_list_return(service, f_name, return_type)


def get_snp500_sector_indices_service_named(service, return_type='full'):
    # By default, dictionary of the major sector indices for the S&P 500, for the named service
    # supported services: yahoo
    # for return_types, pass 'names' to get a list of names or 'tickers' to get a list of tickers only

    f_name = 'snp_sector_indices.csv'
    return _ticker_list_return(service, f_name, return_type)


def get_nasdaq_sector_indices_service_named(service, return_type='full'):
    # By default, dictionary of the major sector indices for the S&P 500, for the named service
    # supported services: yahoo
    # for return_types, pass 'names' to get a list of names or 'tickers' to get a list of tickers only

    f_name = 'nasdaq_sector_indices.csv'
    return _ticker_list_return(service, f_name, return_type)


def get_nyse_sector_indices_service_named(service, return_type='full'):
    # By default, dictionary of the major sector indices for the S&P 500, for the named service
    # supported services: yahoo
    # for return_types, pass 'names' to get a list of names or 'tickers' to get a list of tickers only

    f_name = 'nyse_sector_indices.csv'
    return _ticker_list_return(service, f_name, return_type)


def get_major_metal_etfs_service_named(service, return_type='tickers'):
    # By default, dictionary of the major sector indices for the S&P 500, for the named service
    # supported services: yahoo
    # for return_types, pass 'names' to get a list of names or 'tickers' to get a list of tickers only

    f_name = 'major_metals_etfs.csv'
    return _ticker_list_return(service, f_name, return_type)


def return_commodity_list():
    return ['gld', 'slv', 'pplt', 'pall', 'cl=f', 'ng=f', 'c=f', 's=f', 'kc=f']


def return_crypto_indices():
    return ['^cmc200ex', '^cmc200']


def _ticker_list_return(service, f_name, return_type):
    # use this function to return to a ticker list by passing a supported service and file name
    # supported services: yahoo
    # ticker lists are stored in resources/commonStocks/tickerLists/**service**/**list**
    # pass 'names' to get only a list of names or 'full' to get the entire file returned as a dict

    ticker_list_path.extend([service.lower(), f_name.lower()])
    f_path = osC.create_file_path_string(ticker_list_path)

    if return_type == 'tickers':
        op = fC.return_lines_in_file(f_path, single='yes')
    elif return_type == 'names':
        op = fC.return_column_in_csv_as_list(f_path, 1)
    elif return_type == 'full':
        op = dict()
        keys = fC.return_column_in_csv_as_list(f_path, 1)
        values = fC.return_column_in_csv_as_list(f_path, 0)
        counter = 0
        for key in keys:
            op[key] = values[counter]
            counter = counter + 1
    else:
        raise Exception('Invalid return type passed to _ticker_list_return')

    return op


if __name__ == '__main__':
    test = get_all_tickers(exchange_code="N", force_end_day_data=True)
    # test = get_major_indices_service_named('yahoo', 'names')
    # test = get_major_crypto_coins_service_named('yahoo', 'full')
    # test = get_snp500_sector_indices_service_named('yahoo')
    # test = get_nyse_sector_indices_service_named('yahoo')
    stop = 1
