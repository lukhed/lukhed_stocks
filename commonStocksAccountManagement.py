from resources.aceCommon import osCommon
from resources.aceCommon import fileCommon


def return_selenium_credentials(service):
    """
    :param service: service you want credentials for (to be used with selenium). Current support: 'yahoo'
    :return: dict(), credentials {user: "test", pass: "test", url: "test", portfolio: "name"}
    """

    op_dict = {
        "user": "",
        "pass": "",
        "url": "",
        "portfolio": ""
    }

    selenium_credentials = osCommon.create_file_path_string(
        ['resources', 'commonStocks', 'account', 'seleniumData', 'portfolios.csv'])

    cred_ll = fileCommon.return_lines_in_file(selenium_credentials, header='no')

    for line in cred_ll:
        if line[0] == service:
            op_dict["user"] = line[1]
            op_dict["pass"] = line[2]
            op_dict["url"] = line[3]
            op_dict["portfolio"] = line[4]

    return op_dict


if __name__ == '__main__':
    input("No code to run. Press any key to quit...")
