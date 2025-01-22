from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC
from typing import Optional
import commonSelenium

class Robinhood:
    def __init__(self):
        stop = 1


def main():
    test = rC.basic_request('https://api.robinhood.com/positions/?account_number=5UH76781&nonzero=true', add_user_agent=True)
    stop = 1

if __name__ == '__main__':
    main()
