from lukhed_basic_utils import requestsCommon as rC

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