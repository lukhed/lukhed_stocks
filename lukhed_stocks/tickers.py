from lukhed_basic_utils import osCommon as osC
from lukhed_basic_utils import fileCommon as fC
from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC
from io import StringIO

# A bunch of functions to retrieve ticker lists

class CatWrapper:
    def __inti__(self, keep_daily_cache=True):
        """
        CAT = Consolidated Audit Trail
        
        https://catnmsplan.com/about-cat
        'On July 11, 2012, the U.S. Securities and Exchange Commission (SEC) voted to adopt Rule 613 under 
        Regulation NMS requiring the national securities exchanges and national securities associations 
        listed below (collectively, the SROs) to submit an NMS plan (Plan) to the SEC to create, implement, 
        and maintain a consolidated audit trail (CAT)...'


        """
        sources = None
        self.cache = keep_daily_cache

    def get_ticker_data_by_exchange_code(exchange_or_code, equities_or_options='equities', 
                                         force_retrieval=False, specify_file=None):
        """
        https://catnmsplan.com/reference-data

        The SOD CAT Reportable Equity Securities Symbol Master is published by 6 a.m. ET, and the EOD file 
        is published by 6 p.m. ET. The intraday file is published approximately every 2 hours beginning at 
        10:30 a.m. ET, and includes any updates made to the security master during the day, prior to the 
        EOD file posting. The EOD file contains any securities added during the transaction date. 

        Parameters
        ----------
        exchange_or_code : str()
            _description_
        equities_or_options : _type_, optional
            _description_, by default None
        force_retrieval : bool, optional
            _description_, by default False
        specify_file : str(), optional
            Force pull of a specific file: 'sod', 'eod', or 'intra', by default None and function will pull the 
            file that makes sense based on the curren time and CAT spec.
        """

        equities_sod = "https://files.catnmsplan.com/symbol-master/FINRACATReportableEquitySecurities_SOD.txt"
        equities_eod = "https://files.catnmsplan.com/symbol-master/FINRACATReportableEquitySecurities_EOD.txt"
        equities_intra = "https://files.catnmsplan.com/symbol-master/FINRACATReportableEquitySecurities_Intraday.txt"
        
        data = rC.make_request(equities_eod)
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
            except IndexError:
                test_issue_flag = ""
                error_flag = True


            output_data.append({
                'ticker': ticker,
                'issueName': issue_name,
                'listingExchange': listing_exchange,
                'testIssueFlag': test_issue_flag,
                'fullData': line_list.copy(),
                'error': error_flag
            })


        return output_data



    
    


def get_all_tickers(use_cache_only=False, exchange_code=None, force_end_day_data=False):
    """
    This function gets latest ticker data from sec website, and writes to a cache.
    https://catnmsplan.com/reference-data

    WARMING: This function makes a call to IEX to retrieve if today is trading day. The cost of this transaction
    is 1/50,000 toward limit.

    :param use_cache_only: bool(), use cache only will skip fetching from SEC

    :param exchange_code: str(), if non-none, will return only tickers associated with the exchange code. Find up
                                 to date exchange code at the link:
                                 Primary Listing Exchange
                                    A = NYSE American
                                    N = NYSE
                                    O = OTCBB
                                    P = NYSE ARCA
                                    Q = Nasdaq
                                    U = OTC Equity
                                    V = IEX
                                    Z = Cboe BZX
                                    Else NULL
    :param force_end_day_data: bool(), will always give you end day data instead of intra day.

    :return:
    """
    intra_day_file = osC.create_file_path_string(["resources", "commonStocks", "tickerLists", "all", "intra_day.txt"])
    end_day_file = osC.create_file_path_string(["resources", "commonStocks", "tickerLists", "all", "end_day.txt"])
    start_day_file = osC.create_file_path_string(["resources", "commonStocks", "tickerLists", "all", "start_day.txt"])
    last_updated_file = osC.create_file_path_string(["resources", "commonStocks", "tickerLists", "all", "last_update.json"])


    if use_cache_only:
        pass
    else:
            intra_updated = True
            end_updated = True
            start_updated = True
            if force_end_day_data:
                intra_updated = False
            else:
                try:
                    intra_tickers = rC.requests_get_url_content(
                        "https://files.catnmsplan.com/symbol-master/FINRACATReportableEquitySecurities_Intraday.txt")
                    fC.write_content_to_file(intra_day_file, intra_tickers)
                except:
                    print("Error retrieving intra-day prices")
                    intra_updated = False
                tC.sleep(0.5)

            if force_end_day_data:
                start_updated = False
            else:
                try:
                    start_day = rC.requests_get_url_content(
                        "https://files.catnmsplan.com/symbol-master/CATReportableOptionsSymbolMaster_SOD.txt")
                    fC.write_content_to_file(start_day_file, start_day)
                except:
                    print("Error retrieving start day prices")
                    start_updated = False
                tC.sleep(0.5)

            try:
                end_day = rC.requests_get_url_content(
                    "https://files.catnmsplan.com/symbol-master/FINRACATReportableEquitySecurities_EOD.txt")
                fC.write_content_to_file(end_day_file, end_day)
            except:
                print("Error retrieving end day prices")
                end_updated = False

            date_string = tC.get_date_today(return_string=True)

            if osC.check_if_file_exists(last_updated_file, full_path=1) == 1:
                update_dict = fC.load_json_from_file(last_updated_file)
            else:
                update_dict = {
                    "intraday": "",
                    "sod": "",
                    "eod": ""
                }

            if intra_updated:
                update_dict["intraday"] = date_string
            if start_updated:
                update_dict["sod"] = date_string
            if end_updated:
                update_dict["eod"] = date_string

            fC.dump_json_to_file(last_updated_file, update_dict)


    ch = tC.get_current_hour()


    if force_end_day_data:
        tickers = fC.return_lines_in_file(end_day_file, delimiter="|")
    else:
        trading_day = commonStocksMarketInfo.is_trading_day()
        # return EOD or Intra day based on time and trading day. Note: Start of day has option chain data, not tickers
        if trading_day:
            if 11 > ch >= 18:
                tickers = fC.return_lines_in_file(end_day_file, delimiter="|", header="no")
            else:
                tickers = fC.return_lines_in_file(intra_day_file, delimiter="|", header="no")
        else:
            tickers = fC.return_lines_in_file(end_day_file, delimiter="|")

    if exchange_code is None:
        tickers = [x[0] for x in tickers]
    else:
        tickers = [x[0] for x in tickers if eC.try_except_list_access(2, x) == exchange_code]

    return tickers


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
