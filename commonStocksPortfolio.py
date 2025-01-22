from resources.aceCommon import osCommon
from resources.aceCommon import fileCommon
from resources.aceCommon import timeCommon
from commonStocksWatchLists import get_tickers_from_yahoo_watchlist


def cache_portfolio(service):
    """
    :param service: service where the portfolio is housed. Currently supported: 'yahoo'
    :return: writes portfolio dict/json corresponding to the service to file. Returns a dict
    """

    # Output files
    port_path = _create_portfolio_paths_given_service(service)

    # get portfolio info to write to cache
    t_stamp = timeCommon.create_time_stamp()
    port_dict = get_tickers_from_yahoo_watchlist('Track - Speculation', first_buy_data='yes')
    port_dict["lastUpdate"] = t_stamp

    fileCommon.dump_json_to_file(port_path, port_dict)

    return port_dict


def get_portfolio_from_cache(service):
    """
    :param service: string: 'yahoo'
    :return: dict(): {tickers: [list, of, tickers], lastUpdate: timestamp, etc.}
    """

    op_dict = {
        "tickers": [],
        "lastUpdate": ""
    }

    portfolio_paths = _create_portfolio_paths_given_service(service)
    port_path = portfolio_paths["portPath"]
    port_stamp_path = portfolio_paths["stampPath"]

    port_json = fileCommon.load_json_from_file(port_path)
    last_update = fileCommon.read_single_line_from_file(port_stamp_path)

    op_dict["tickers"] = port_json["tickers"]
    op_dict["lastUpdate"] = last_update

    return op_dict


def _create_portfolio_paths_given_service(service):
    """
    :param service: string, 'yahoo'
    :return: string, with port path
    """

    service = service.lower()
    port_fname = service.lower() + '.json'
    port_path = osCommon.create_file_path_string(['resources', 'commonStocks', 'tickerLists', 'portfolios', port_fname])

    return port_path


if __name__ == '__main__':
    cache_portfolio('yahoo')
