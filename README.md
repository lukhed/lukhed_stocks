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
- [Robinhood Wrapper](#robinhood-wrapper) - Wrapper for Robinhood's public API endpoints. Provides access to stock 
  data, fundamentals, charts, and popular stock lists without requiring authentication. Auth methods coming later.
- [Polygon.io Wrapper](#polygonio-wrapper) - Wrapper for Polygon.io's API. Provides free access to market status and holiday information with up to 5 API requests per minute and 500 requests per day.
- [TradingView Wrapper](#tradingview-wrapper) - Wrapper for TradingView's stock screener. Provides access to 
  stock lists, filters by sector/industry, and customizable screening criteria.


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

## Robinhood Wrapper

### Setup
No authentication required. The wrapper provides access to Robinhood's public API endpoints.

```python
from lukhed_stocks.robinhood import Robinhood

rh = Robinhood()
```

### Basic Usage Examples
```python
# Get basic instrument data
basic_data = rh.get_basic_data('AAPL')
multiple_stocks = rh.get_basic_data(['AAPL', 'TSLA', 'MSFT'])

# Get fundamental data
fundamentals = rh.get_fundamentals('AAPL')

# Get chart data for different time spans
daily_chart = rh.get_basic_chart_data('AAPL', span='day')
yearly_chart = rh.get_basic_chart_data('AAPL', span='year', extended_hours=True)
```

### Popular Lists
```python
# Get most held stocks on Robinhood
top_50 = rh.get_most_held_instruments(top_x=50)
symbols_only = rh.get_most_held_instruments(return_symbols_only=True)

# Search for instruments
search_results = rh.search_instruments_by_symbol_keyword('TECH')
```

### API Rate Limiting
The wrapper includes built-in rate limiting to be respectful of Robinhood's servers.

```python
# Adjust delay between API calls (default is 0.5 seconds)
rh = Robinhood(api_delay=1.0)

# Disable user agent randomization if needed
rh = Robinhood(random_user_agent=False)
```


## Polygon.io Wrapper

### Setup
Setup the API auth once and use it across hardware. To setup, instantiate the class and follow the prompts to enter 
your [Polygon.io API key](https://polygon.io/dashboard/keys). By default, your private github repo is used for key 
management (you will need a github account and token).

```python
# Github setup
from lukhed_stocks.polygon import PolygonIo

# Default instantiation uses github key_management
poly = PolygonIo()
```

```python
# If you want to use local hardware key storage only
poly = PolygonIo(key_management='local')
```

### Usage Examples After Setup
```python
poly = PolygonIo()

# Get current market status
market_status = poly.get_market_status_now()

# Get upcoming market holidays
holidays = poly.get_upcoming_market_holidays()

# Check if market is open today
is_open = poly.is_market_open_today()
```

### API Rate Limiting
The wrapper includes built-in rate limiting. The free tier allows 5 API requests per minute and 500 requests per day.

```python
# Adjust delay between API calls (default is 1 second)
poly = PolygonIo(api_delay=2.0)
```

### Skip Setup with Auth Dictionary
```python
# Provide auth data directly to skip setup prompts
auth_data = {"key": "your_api_key_here"}
poly = PolygonIo(auth_dict=auth_data)
```


## TradingView Wrapper

### Setup
No authentication required. The wrapper provides access to TradingView's stock screener endpoints.

```python
from lukhed_stocks.tradingview import TradingView

tv = TradingView()
```

### Basic Usage Examples
```python
# Get all stocks with default TradingView filters and columns
all_stocks = tv.screener_get_all_stocks()

# Get stocks by index
dow_stocks = tv.screener_get_stocks_by_index('dow')
sp500_stocks = tv.screener_get_stocks_by_index('s&p')
nasdaq_stocks = tv.screener_get_stocks_by_index('nasdaq')
russell_stocks = tv.screener_get_stocks_by_index('russel 2000')

# Get stocks at new highs or lows
new_52w_highs = tv.screener_new_highs_lows(new_high_or_low='high', month_time_frame=12)
new_3m_lows = tv.screener_new_highs_lows(new_high_or_low='low', month_time_frame=3)
all_time_highs = tv.screener_new_highs_lows(new_high_or_low='high', month_time_frame='all time')
```

### Filtering Stock Lists
```python
# Filter by sector or industry
tech_stocks = tv.filter_stock_list_by_sector('Technology', all_stocks['data'])
multiple_sectors = tv.filter_stock_list_by_sector(['Healthcare', 'Finance'], all_stocks['data'])
industry_filtered = tv.filter_stock_list_by_industry('Software', all_stocks['data'])

# Get sector/industry information
sectors = tv.get_all_sectors_in_list(all_stocks['data'])
industries = tv.get_all_industries_in_list(all_stocks['data'])
breakdown = tv.get_sector_industry_breakdown_of_list(all_stocks['data'])
tickers = tv.get_unique_stock_tickers_in_list(all_stocks['data'])
```

### Customizing Screener Columns
```python
# Use predefined column sets
tv.set_stock_screener_columns_overview()
tv.set_stock_screener_columns_performance()
tv.set_stock_screener_columns_valuation()
tv.set_stock_screener_columns_dividends()
tv.set_stock_screener_columns_technicals()
tv.set_stock_screener_columns_profitiability()
tv.set_stock_screener_columns_per_share()

# Add custom columns
tv.custom_define_columns(["name", "description", "Perf.W", "Perf.1M", "Perf.3M", "Perf.6M", "Perf.YTD", "exchange"])

# Add to existing columns instead of replacing
tv.set_stock_screener_columns_time_period_performance(add_to_current_columns=True)

# Reset to defaults
tv.reset_screener_columns()
```

### Custom Filters
```python
# Add custom filters
custom_filter = {
    "left": "market_cap_basic",
    "operation": "egreater",
    "right": 1000000000
}
tv.add_screener_filters(custom_filter)

# Reset filters to default
tv.reset_screener_filters()

# Clear all filters
tv.clear_screener_filters()

# Set completely custom filter
tv.set_custom_screener_filter(custom_filter)
```

### Supported Index Filters
The wrapper supports filtering by the following indices (check `tv.index_lookup` for full list):
- Dow Jones: `'dow'`
- S&P 500: `'s&p'`
- Nasdaq Composite: `'nasdaq'`
- Nasdaq 100: `'nasdaq 100'`
- Russell 2000: `'russel 2000'`
- And many more sector-specific indices


## Responsible Data Usage
- Each method or wrapper in the documentation lists the source that is utilized by default
- Below is information related to data retrieval and usage for each source

### CAT Data Usage
CAT Data is pulled from [this page](https://www.catnmsplan.com/reference-data). They provide 
a [legal notice here](https://www.catnmsplan.com/legal-notice).

### Wikipedia Data Usage
Wikipedia content is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
For more details on the terms of use, please refer to the 
[Wikimedia Foundation's Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use).

### Synth
Full Synth terms are found [here](https://synthfinance.com/terms). This library provides access to synth:
- Images, free to use if attribution is provided (please confirm with synthfinance.com or the terms above)

### Robinhood Data Usage
Data is accessed through Robinhood's public API endpoints without authentication. This wrapper is intended for 
educational and research purposes. Please respect Robinhood's terms of service and API usage guidelines. 
Users are responsible for ensuring their usage complies with Robinhood's policies.

### Polygon.io Data Usage
Data is accessed through Polygon.io's API. Free tier provides up to 5 API requests per minute and 500 requests per day. 
For higher volume usage, please visit [Polygon.io's pricing page](https://polygon.io/pricing). 
Users are responsible for ensuring their usage complies with Polygon.io's terms of service and API usage limits.

### Tradingview Data Usage
I am currently trying to remove trading view as a source, as their policy is restrictive and confusing. 
Please read [trading view policies here](https://www.tradingview.com/policies/)
