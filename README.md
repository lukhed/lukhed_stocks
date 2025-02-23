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
  management and convenience functions to the unopinionated wrapper which provides auth, quotes, history, options, account info and more.


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

### Setup
Setup the API auth once and use it across hardware. To setup, instantiate with schwab_api_setup=True. By default, your private github repo is used for key mangement (you will need a github account and token). Setup will ask for your [Schwab developer](https://developer.schwab.com/) app key, secret, and callback url, then take you through authenticating with Schwab.<br><br>Note: this wrapper uses [schwab-py](https://pypi.org/project/schwab-py/) for actual Schwab auth. See the documentation there for any issues or questions in setting up your schwab account.

```python
#Github setup
schwab = SchwabPy(schwab_api_setup=True)
```

```python
#Local setup (won't work across hardware)
schwab = SchwabPy(schwab_api_setup=True, key_management='local')
```

### Usage Examples After Setup
```python
schwab = SchwabPy()
quotes = schwab.get_stock_quote(['allt', 'way', 'pplt', 'impuy'])
price = schwab.get_stock_price('allt')
low = schwab.get_stock_52w_low('gld')
percent_below_high = schwab.get_percent_below_52w_high('aapl')
```

### Cache Option
If prices are stale when using this wrapper (e.g., after market) or realtime price is not needed for your analysis, you can use cache to speed up calls.

```python
schwab = SchwabPy(use_ticker_cache=True)
quotes = schwab.get_stock_quote(['allt', 'way', 'pplt', 'impuy'])   # 'allt' in cache
price = schwab.get_stock_price('allt')  # retrieve price from cache
```

### Utilizing schwab-py
My wrapper is built for key management, advanced analysis, and ease of use. The exposed methods are recommended when using my wrapper, but you can access any of the endpoints available from [schwab-py](https://pypi.org/project/schwab-py/) like below.

```python
schwab.api.get_price_history_every_minute("ALLT")
```


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
