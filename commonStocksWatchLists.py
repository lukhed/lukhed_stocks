from resources.aceCommon import timeCommon
from resources.aceCommon import selleniumCommon
from resources.aceCommon import listWorkCommon as lC
from commonStocksAccountManagement import return_selenium_credentials


def _create_selenium_api(service, move_to_watchlist_page=None):
    """
    :param service: string, current support: 'yahoo'
    :param move_to_watchlist_page: will traverse to the watch list if string specified (e.g. "Track - Speculation")
    :return: a selenium object after logging into the specified service. Currently support: 'yahoo'
    """

    selenium_credentials = return_selenium_credentials(service)

    user = selenium_credentials["user"]
    password = selenium_credentials["pass"]
    url = selenium_credentials["url"]
    portfolio = selenium_credentials["portfolio"]

    browser = selleniumCommon.create_browswer_object_sel(url)

    if service.lower() == 'yahoo':
        # click link to login
        selleniumCommon.wait_for_page(browser, '// *[ @ id = "Col1-0-Portfolios-Proxy"] / section / div / a', 10)
        link = browser.find_element_by_xpath('// *[ @ id = "Col1-0-Portfolios-Proxy"] / section / div / a')
        link.click()

        # enter user name and press enter
        selleniumCommon.wait_for_page(browser, '//*[@id="login-username"]', 10)
        input_email = browser.find_element_by_xpath('//*[@id="login-username"]')
        selleniumCommon.send_keys_to_browser(input_email, user, press_enter='yes')

        # enter password and press enter
        selleniumCommon.wait_for_page(browser, '//*[@id="login-passwd"]', 10)
        input_password = browser.find_element_by_xpath('//*[@id="login-passwd"]')
        selleniumCommon.send_keys_to_browser(input_password, password, press_enter='yes')

        # move to watch_list if specified
        if move_to_watchlist_page is not None:

            # wait for watch lists to load, then click the specified watchlist
            selleniumCommon.wait_for_page(
                browser, '//*[@id="Col1-0-Portfolios-Proxy"]/main/table/tbody/tr[1]/td[1]', 10)
            link = browser.find_element_by_link_text(move_to_watchlist_page)
            link.click()

            # wait for watlist to load, then click something
            selleniumCommon.wait_for_page(
                browser, '//*[@id="Lead-3-Portfolios-Proxy"]/main/div[2]/section/ul/li[2]/a', 10)
            link = browser.find_element_by_xpath('//*[@id="Lead-3-Portfolios-Proxy"]/main/div[2]/section/ul/li[2]/a')
            link.click()

    return browser


def get_tickers_from_yahoo_watchlist(watch_list_name, first_buy_data=None):
    """
    :param watch_list_name: string, as available from yahoo watch list website
    :param first_buy_data: if not none, will get additional buy information associated with each stock in the watchlist
    :return: list or dict depending on first_buy_data parameter
    """
    selenium_api = _create_selenium_api('yahoo', move_to_watchlist_page=watch_list_name)
    ticker_list = list()
    row_list = list()
    op_dict = {
        "tickers": [],
        "firstBuyList": [],
        "purchasePriceList": []
    }

    for i in range(1, 100):
        temp_element = (
            '/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[4]/main/div[2]/div/table/tbody[' +
            str(i) + ']/tr[2]/td[2]/div[1]/a'
        )

        try:
            selleniumCommon.wait_for_page(selenium_api, temp_element, 10, auto_quit_browser='no')
            ticker_element = selenium_api.find_element_by_xpath(temp_element)
            ticker_list.append(ticker_element.text)
            row_list.append(i)
        except:
            break

    if first_buy_data is None:
        return ticker_list
    else:
        first_buy_dict = _get_first_buy_data(selenium_api, row_list)
        op_dict["tickers"] = ticker_list
        op_dict["firstBuyList"] = first_buy_dict["dateList"]
        op_dict["purchasePriceList"] = first_buy_dict["priceList"]
        return op_dict


def _get_first_buy_data(selenium_api, ticker_row_list):
    """
    :param ticker_row_list: list of ints, each ticker row you want a date for
    :return: dictionary, with two lists, first buy date and purchase price
    """

    first_buy_list = list()
    purchase_price_list = list()

    op_dict = {
        "dateList": first_buy_list,
        "priceList": purchase_price_list
    }

    for i in ticker_row_list:
        # expand the list
        temp_button_path = (
                '//*[@id="Lead-3-Portfolios-Proxy"]/main/div[2]/div/table/tbody[' + str(i) + ']/tr[2]/td[1]/button'
        )
        temp_button = selenium_api.find_element_by_xpath(temp_button_path)
        temp_button.click()

        # retrieve buy dates
        temp_date_list = []
        temp_price_list = []
        for a in range(1, 100):

            temp_date_path = (
                '//*[@id="Lead-3-Portfolios-Proxy"]/main/div[2]/div/table/tbody[' + str(i) +
                ']/tr[3]/td/table/tbody/tr[' + str(a) + ']/td[1]/input'
            )

            temp_purchase_path = (
                    '//*[@id="Lead-3-Portfolios-Proxy"]/main/div[2]/div/table/tbody[' + str(i) +
                    ']/tr[3]/td/table/tbody/tr[' + str(a) + ']/td[3]/input'
            )

            try:
                temp_date = selenium_api.find_element_by_xpath(temp_date_path).get_attribute("value")
                temp_date_list.append(temp_date)
                temp_price = selenium_api.find_element_by_xpath(temp_purchase_path).get_attribute("value")
                temp_price_list.append(temp_price)
            except:
                first_buy_list.append(timeCommon.sort_date_list(temp_date_list)[0])
                temp_price_list = lC.convert_all_list_values("float", temp_price_list)
                temp_price_list.sort()
                purchase_price_list.append(temp_price_list[0])
                break

    return op_dict


if __name__ == '__main__':
    input("No code to run. Press any key to quit...")
