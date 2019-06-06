import psycopg2
import pandas as pd
from pandas_datareader import data as web
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
import bs4
from bs4 import BeautifulSoup
import requests
import datetime

# Connecting to the databse
conn = psycopg2.connect(
    database = 'cuzegotk',
    user = 'cuzegotk',
    password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
    host = 'raja.db.elephantsql.com'
)
cur = conn.cursor()
cur.execute('SELECT * FROM portfolio')
portfolio_list = cur.fetchall()
cur.execute('SELECT * FROM watchlist')
watchlist_list = cur.fetchall()
cur.close()
conn.close()

# Transforms dataset to usuable format
def transformData(name, value, dataset):
    for i in range(len(name)):
        if value == '-':
            dataset[name[i]] = float(0)
        elif type(value[i]) == str:
            dataset[name[i]] = float(value[i].replace(',',''))
        else:
            continue
    return dataset

# Takes the SQL query from database and creates a set of features using web scraping and API calls to extract data
def getFeatures(querylist):

    featurelist = []
    for t in querylist:
        # Yahoo API to extract historical stock prices
        data = pd.DataFrame()
        data = web.DataReader(t[0], 'yahoo', start, end)
        n = len(data) - 1
        weekly = (data['Adj Close'] / data['Adj Close'].rolling(5).mean())[n]
        monthly = (data['Adj Close'] / data['Adj Close'].rolling(21).mean())[n]
        yearly = (data['Adj Close'] / data['Adj Close'].rolling(250).mean())[n]

        # Web scrape off of yahoo finance to get the sector code
        r = requests.get('https://ca.finance.yahoo.com/quote/{}/profile?p={}'.format(t[0],t[0]))
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        container = soup.findAll('p', {'class': 'D(ib) Va(t)'})[0]
        sector = container.findChildren()[1].text

        # Web scrape off of marketwatch.com for analyst recommendation on stocks
        r = requests.get('https://www.marketwatch.com/investing/stock/{}/analystestimates'.format(t[0]))
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        container = soup.findAll('td', {'class': 'recommendation'})[0]
        rating = container.text.strip()

        # Income Statement Metrics from marketwatch.com
        r = requests.get('https://ca.finance.yahoo.com/quote/{}/financials?p={}'.format(t[0],t[0]))
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
        r = requests.get('https://ca.finance.yahoo.com/quote/{}/balance-sheet?p={}'.format(t[0],t[0]))
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
        transformData(name, value, dataset)

        # Create dataset for our features
        features = pd.DataFrame(index=[t[0]])

        # Calculate our features using the data we extracted above
        features['ticker'] = t[0]
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

        featurelist.append(features.values)

    return featurelist

# Takes in a set of features and the type of database query to insert new features into the database
def updateDatabase(features, querylist='portfolio'):

    conn = psycopg2.connect(
        database = 'cuzegotk',
        user = 'cuzegotk',
        password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
        host = 'raja.db.elephantsql.com'
    )
    cur = conn.cursor()
    if querylist == 'portfolio':
        modelrating = fitModel(features)
        for i,j in enumerate(modelrating):
            print(j, features[i][0][0])
            cur.execute('UPDATE portfolio SET modelrating = %s WHERE ticker = %s', (j, features[i][0][0]))
            conn.commit()
        for i in features:
            cur.execute('UPDATE portfolio SET marketrating = %s WHERE ticker = %s', (i[0][-1], i[0][0]))
            conn.commit()
    else:
        modelrating = fitModel(features)
        for i,j in enumerate(modelrating):
            print(j, features[i][0][0])
            cur.execute('UPDATE watchlist SET modelrating = %s WHERE ticker = %s', (j, features[i][0][0]))
            conn.commit()
        for i in features:
            cur.execute('UPDATE watchlist SET marketrating = %s WHERE ticker = %s', (i[0][-1], i[0][0]))
            conn.commit()
    cur.close()
    conn.close()

# Imports trained model using pickle to predict the rating of the stock based on the features extracted
def fitModel(features):
    filename = 'model.pkl'
    infile = open(filename, 'rb')
    model = pickle.load(infile)
    infile.close()
    pred = []
    # Labels for encoding
    sector_columns = ['Basic Materials', 'Communication Services', 'Consumer Cyclical',
       'Consumer Defensive', 'Energy', 'Financial Services', 'Healthcare',
       'Industrials', 'Real Estate', 'Technology', 'Utilities']
    labels = ['Buy', 'Hold', 'Overweight', 'Sell', 'Underweight']

    for i in features:
        # Encoding the sector and label columns for our model
        encoded_sector = [0] * len(sector_columns)
        index = sector_columns.index(i[0][1])
        encoded_sector[index] = 1
        X = np.array([*encoded_sector, *i[0][2:-1]]).reshape(1,-1)
        # Transforming the encoded labels back to string format
        pred.append(labels[np.argmax(model.predict_proba(X))])

    return pred


# Datetime of today's date and the previous year
start = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
end = datetime.datetime.now().strftime('%Y-%m-%d')

# Grabbing new features of the stocks in our portfolio and watchlist database
portfolio_features = getFeatures(portfolio_list)
watchlist_features = getFeatures(watchlist_list)
# Updating the market rating and the model prediction for the stocks in our database
updateDatabase(portfolio_features, 'portfolio')
updateDatabase(watchlist_features, 'watchlist')
