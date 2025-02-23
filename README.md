# lukhed_stocks
A collection of stocks analysis utility functions and API wrappers. Repo is in development. Please note that 
you are responsible for how you access and use the data. 
See the [responsible data usage section](#responsible-data-usage) for more info.


## Installation
```bash
pip install lukhed-stocks
```


## TOC
<!-- no toc -->
[Available Functions](#available-functions)<br>
[Available Wrappers](#available-wrappers)<br>
[Responsible Data Usage](#responsible-data-usage)

## Available Functions
- [Ticker Data Functions](#ticker-functions) - Utilizing various sources (default sources require no api key).
  - [Get Tickers By Exchange](#get-tickers-by-exchange)
  - [Get Tickers By Index](#get-tickers-by-index)
  - [Get Company Logo by Ticker](#get-company-logo-by-ticker)
  
## Available Wrappers
- [CAT Wrapper](#cat-wrapper) - Conolidated Audit Trail (CAT) for exchange data provided by [CAT Webpage](https://catnmsplan.com/)
- [Wikipedia Stocks](#wikipedia-stocks) - For obtaining various stock data from Wikipedia (various pages)
- [Schwab Wrapper](#schwab-wrapper) - Wrapper for [schwab-py wrapper](https://pypi.org/project/schwab-py/). Adds key 
  management and convenience functions to the unopinionated wrapper providing (auth, quotes, history, options, 
  account info and more.)


## Ticker Functions

### Tickers Import
```python
from lukhed_stocks import tickers
```

### Get Tickers By Exchange
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

### Get Tickers By Index
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


### Get Company Logo by Ticker
```python
logo_url = tickers.get_company_logo('ALLT')
logo_url_with_download = tickers.get_company_logo('WAY', output_file='way.png')
```

| Function | Default Source|
|------------------------------|--------------|
| tickers.get_company_log      | [Synth](#synth)|



## CAT Wrapper
Documentation coming soon.

## Wikipedia Stocks
Documentation coming soon.

## Schwab Wrapper
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

### Synth
Full Synth terms are found [here](https://synthfinance.com/terms). This library provides access to synth:
- Images, free to use if attribution is provided (please confirm with synthfinance.com or the terms above)

### Tradingview Data Usage
I am currently trying to remove trading view as a source, as their policy is restrictive and confusing. Please read [trading view policies here](https://www.tradingview.com/policies/)
