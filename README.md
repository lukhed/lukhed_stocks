# lukhed_stocks
A collection of stocks analysis utility functions and API wrappers built with personal use in mind. Basic functionality is available now, and this repo is in development. Please note that you are responsible for how you access and use the data. See the [responsible data usage section](#responsible-data-usage) for more info.


## Installation
```bash
pip install lukhed-stocks
```


## TOC
<!-- no toc -->
  - [Available Functions](#available-functions)
  - [Available Wrappers](#available-wrappers)
  - [CAT Wrapper](#cat-wrapper)
  - [Wikipedia Stocks](#wikipedia-stocks)
  - [Responsible Data Usage](#responsible-data-usage)
    - [CAT Data Usage](#cat-data-usage)
    - [Wikipedia Data Usage](#wikipedia-data-usage)
    - [Tradingview Data Usage](#tradingview-data-usage)

## Available Functions
- [Get Exchange & Index Data](#Get-Exchange-and-Index-Data) - Utilizing various sources (free or with API key) to provide ticker data for exchanges.
  
## Available Wrappers
- [CAT Wrapper](#CAT-Wrapper) - Conolidated Audit Trail (CAT) for exchange data provided by [CAT Webpage](https://catnmsplan.com/)
- [Wikipedia Stocks](#Wikipedia-Wrapper) - For obtaining various stock data from Wikipedia (various pages)


## Get Exchange and Index Data

### Tickers Import
```python
from lukhed_stocks import tickers
```

### Get Exchange Data Functions
Provides a list of stock data for the given exchange. Each function can optionally be called with 'tickers_only' parameter to return a list of strings only. These functions utilize [CAT data](https://catnmsplan.com/) by default  and do not require an API key.

```python
nasdaq = tickers.get_nasdaq_stocks()
nyse = tickers.get_nyse_stocks(tickers_only=True)
otc = tickers.get_otc_stocks()
iex = tickers.get_iex_stocks(tickers_only=True)
```

| Function | Default Source|
|------------------------------|--------------|
| tickers.get_nasdaq_stocks    | [CAT](#cat-data-usage)|
| tickers.get_nyse_stocks      | [CAT](#cat-data-usage)|
| tickers.get_otc_stocks       | [CAT](#cat-data-usage)|
| tickers.get_iex_stocks       | [CAT](#cat-data-usage)|

### Get Index Data Functions
Provides a list of stock data for the given index. Each function can optionally be called with 'tickers_only' parameter to return a list of strings only. The default source for each function does 
not require an API key.

```python
sp500 = tickers.get_sp500_stocks()
djia = tickers.get_dow_stocks(tickers_only=True)
otc = tickers.get_russell2000_stocks()
```

| Function | Default Source|
|---------------------------------|--------------|
| tickers.get_sp500_stocks        | [Wikipedia](#cat-data-usage)|
| tickers.get_dow_stocks          | [Wikipedia](#wikipedia-data-usage)|
| tickers.get_russell2000_stocks  | [TradingView](#tradingview-data-usage)|


## CAT Wrapper
Documentation coming soon.

## Wikipedia Stocks
Documentation coming soon.


## Responsible Data Usage
- Each method or wrapper in the documentation lists the source that is utilized by default
- Below is information related to data retrieval and usage for each source

### CAT Data Usage
CAT Data is pulled from [this page](https://www.catnmsplan.com/reference-data). They provide a [legal notice here](https://www.catnmsplan.com/legal-notice).

### Wikipedia Data Usage
Wikipedia content is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
For more details on the terms of use, please refer to the 
[Wikimedia Foundation's Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use).

### Tradingview Data Usage
I am currently trying to remove trading view as a source, as their policy is restrictive and confusing. Please read trading view policies here: 'https://www.tradingview.com/policies/
