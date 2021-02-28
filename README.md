Script to query ENTSO-E database using [entsoe-py](https://github.com/EnergieID/entsoe-py) for production data and compute corresponding emissions to plot this kind of graphic:

See all plots available here: [plots](./plots).

To make a new plot:
## Step 1: install librairies
```
pip install pandas
pip install matplotlib
pip install entsoe-py
```

## Step 2: clone repository locally
```
cd path/to/folder
git clone <repo_name>
```

## Step 3: enter parameters
- open `data_analyis_request_ENTSO_E.py`
- replace `${{ secrets.TOKEN_API }}` with your API key
- for yearly plots:
  - change range
  - comment `for month in range(1,13):`
  - choose `start = pd.Timestamp(year=year, month=1, day=1, tz='Europe/Brussels')` and `end = pd.Timestamp(year=year, month=12, day=31, tz='Europe/Brussels')`
- for monthly plots:
  - uncomment `for month in range(1,13):`
  - choose `start = pd.Timestamp(year=year, month=month, day=1, tz='Europe/Brussels')` and `end = pd.Timestamp(year=year, month=month, day=start.daysinmonth, tz='Europe/Brussels')`
- choose countries in `country_code` (see list [here](https://github.com/EnergieID/entsoe-py/blob/master/entsoe/mappings.py))

## Step 4: run script `data_analyis_request_ENTSO_E`
Wait... and find your new plots in `/plots`

## Step 5: push new data and plots to remote repo so everyone benefits from your query
