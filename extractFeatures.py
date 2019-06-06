# Import Libraries for data extraction
import numpy as np
import pandas as pd
from pandas_datareader import data as web
import datetime
import requests
import bs4
from bs4 import BeautifulSoup
import psycopg2
import os
import sys

# Sets todays/last years date using datetime
day = datetime.datetime.now().day
month = datetime.datetime.now().month
year = datetime.datetime.now().year
last_year = year - 1

# Todays date
start = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
# Last year from todays date
end = datetime.datetime.now().strftime('%Y-%m-%d')

# Takes in arguments from the command line
tickers = sys.argv
del tickers[0]

# Function that transforms extracted data to usuable format, to be called later
def transformData(name, value):
    for i in range(len(name)):
        if value == '-':
            dataset[name[i]] = float(0)
        elif type(value[i]) == str:
            dataset[name[i]] = float(value[i].replace(',',''))
        else:
            continue
    return dataset

# Loop data extraction process based on list of input ticker arguments

for t in tickers:
    try:
        # Yahoo API to extract historical stock prices
        data = pd.DataFrame()
        data = web.DataReader(t, 'yahoo', start, end)
        n = len(data) - 1
        weekly = (data['Adj Close'] / data['Adj Close'].rolling(5).mean())[n]
        monthly = (data['Adj Close'] / data['Adj Close'].rolling(21).mean())[n]
        yearly = (data['Adj Close'] / data['Adj Close'].rolling(250).mean())[n]

        # Web scrape off of yahoo finance to get the sector code
        r = requests.get('https://ca.finance.yahoo.com/quote/{}/profile?p={}'.format(t,t))
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        container = soup.findAll('p', {'class': 'D(ib) Va(t)'})[0]
        sector = container.findChildren()[1].text

        # Web scrape off of marketwatch.com for analyst recommendation on stocks
        r = requests.get('https://www.marketwatch.com/investing/stock/{}/analystestimates'.format(t))
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        container = soup.findAll('td', {'class': 'recommendation'})[0]
        rating = container.text.strip()

        # Income Statement Metrics from marketwatch.com
        r = requests.get('https://ca.finance.yahoo.com/quote/{}/financials?p={}'.format(t,t))
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        revenue = soup.findAll('tr', {'class':'Bdbw(1px) Bdbc($c-fuji-grey-c) Bdbs(s) H(36px)'})[1]
        gross_profit = soup.findAll('tr', {'class':'Bdbw(0px)! H(36px)'})[0]
        net_income = soup.findAll('tr', {'class':'Bdbw(1px) Bdbc($c-fuji-grey-c) Bdbs(s) H(36px)'})[21]

        # Revenues, Gross Profits, Net Incomes for last 3 years
        rev = revenue.findChildren()[3].text
        rev_1yr = revenue.findChildren()[4].text
        rev_2yr = revenue.findChildren()[6].text
        gross = gross_profit.findChildren()[3].text
        gross_1yr = gross_profit.findChildren()[4].text
        gross_2yr = gross_profit.findChildren()[6].text
        net = net_income.findChildren()[3].text
        net_1yr = net_income.findChildren()[4].text
        net_2yr = net_income.findChildren()[6].text

        # Balance Sheet Metrics from marketwatch.com
        r = requests.get('https://ca.finance.yahoo.com/quote/{}/balance-sheet?p={}'.format(t,t))
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        current_assets = soup.findAll('tr', {'class': 'Bdbw(1px) Bdbc($c-fuji-grey-c) Bdbs(s) H(36px)'})[7]
        total_assets = soup.findAll('tr', {'class': 'Bdbw(0px)! H(36px)'})[0]
        current_liabilities = soup.findAll('tr', {'class': 'Bdbw(1px) Bdbc($c-fuji-grey-c) Bdbs(s) H(36px)'})[19]
        total_liabilities = soup.findAll('tr', {'class': 'Bdbw(0px)! H(36px)'})[1]
        total_equity = soup.findAll('tr', {'class': 'Bdbw(1px) Bdbc($c-fuji-grey-c) Bdbs(s) H(36px)'})[34]

        # Current Asset, Total Asset, Current Liabilities, Total Liabilities, Total Equity
        c_assets = current_assets.findChildren()[3].text
        t_assets = total_assets.findChildren()[2].text
        c_liabilities = current_liabilities.findChildren()[3].text
        t_liabilities = total_liabilities.findChildren()[2].text
        t_equity = total_equity.findChildren()[2].text

        # Name/Value pair of our metrics
        name = ['revenue', 'revenue1yr', 'revenue2yr', 'gross', 'gross1yr', 'gross2yr', 'net', 'net1yr', 'net2yr', 'current assets', 'total assets', 'current liabilities', 'total liabilities', 'total equity']
        value = [rev, rev_1yr, rev_2yr, gross, gross_1yr, gross_2yr, net, net_1yr, net_2yr, c_assets, t_assets, c_liabilities, t_liabilities, t_equity]
        dataset = {}

        # Run function to transform data
        transformData(name, value)

        # Create dataset for our features
        features = pd.DataFrame(index=[t])

        # Calculate our features using the data we extracted above
        features.index.name = 'Ticker'
        features['sector'] = sector
        features['WeeklyMA'], features['MonthlyMA'], features['YearlyMA'] = round(weekly,5), round(monthly,5), round(yearly,5)
        features['gross/revenue'] = round(dataset['gross']/dataset['revenue'],5)
        features['gross/revenue-1yr'] = round(dataset['gross1yr']/dataset['revenue1yr'],5)
        features['gross/revenue-2yr'] = round(dataset['gross2yr']/dataset['revenue2yr'],5)
        features['net/revenue'] = round(dataset['net']/dataset['revenue'],5)
        features['net/revenue-1yr'] = round(dataset['net1yr']/dataset['revenue1yr'],5)
        features['net/revenue-2yr'] = round(dataset['net2yr']/dataset['revenue2yr'],5)
        features['current-ratio'] = round(dataset['current assets']/dataset['current liabilities'],5)
        features['debt-equity'] = round(dataset['total liabilities']/dataset['total equity'],5)
        features['debt-asset'] = round(dataset['total liabilities']/dataset['total assets'],5)
        features['rating'] = rating

        # Checks to see if our dataset exists within the directory and creates a CSV file format of features
        if os.path.isfile('./features.csv'):
            with open('./features.csv', 'a') as f:
                features.to_csv(f, sep=',', header=False)
        else:
            with open('./features.csv', 'w') as f:
                features.to_csv(f, sep=',')

    except:
        continue

    # Checks for features.csv in directory
    if os.path.isfile('./features.csv'):

        # Converts features.csv into a pandas dataframe
        csv = pd.read_csv('./features.csv')
        # Connect to SQL database
        conn = psycopg2.connect(database = 'cuzegotk',user = 'cuzegotk',password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',host = 'raja.db.elephantsql.com')
        cur = conn.cursor()
        cur.execute('SELECT ticker FROM features')
        # Query list of all tickers currently within database
        ticker_list = ['%s' % i  for i in cur.fetchall()]

        # If new set of features is not found within the database, they are inserted into our database
        for i in csv.values:
            if i[0] not in ticker_list:
                cur.execute('INSERT INTO features VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', tuple(i))
                conn.commit()
            else:
                continue
        cur.close()
        conn.close()
    else:
        pass
