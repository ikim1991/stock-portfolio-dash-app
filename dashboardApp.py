# Import libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

import psycopg2
import numpy as np
import pandas_datareader.data as web
import datetime
import functionality as f

# Initialize app by predefined state values
state = {
    'columns':{
        'portfolio': ['Ticker', 'Shares', 'Last Price', 'Change(%)', 'Book Cost', 'Market Value', 'Unrealized Gain(%)', 'Model Prediction', 'Analyst Rating'],
        'total': ['Number of Stocks', 'Portfolio Book Cost', 'Portfolio Market Value', 'Unrealized Portfolio Gain(%)'],
        'watchlist': ['Ticker', 'Last Price', 'Last close', 'Volume', 'Change(%)', 'Model Prediction', 'Analyst Rating']
    },
    'equity_list': f.initialize_dropdown()
}

# Dash Application
app = dash.Dash()
server = app.server

# Dash Application Components
app.layout = html.Div([
    html.H1(
        children='Stock Portfolio App',
        style={
            'width': '100%',
            'text-align': 'center'
        }
    ),
    html.Hr(),
    html.H2(
        children='My Portfolio',
        style={
            'width': '100%'
        }
    ),
    html.Hr(),
    html.Div([
        dcc.Dropdown(
            id='portfolio-ticker',
            placeholder='Enter Stock Ticker',
            options=[{'label':i[0]+' - '+i[1], 'value':i[1]} for i in state['equity_list']],
            style={
                'width':'43%'
            }
        ),
        dcc.Input(
            id='stock-price',
            placeholder='Price per Share',
            type='number',
            name='price'
        ),
        dcc.Input(
            id='stock-shares',
            placeholder='Number of Shares',
            type='number',
            name='shares'
        ),
        html.Button(
            children='Add to Portfolio',
            id='add-portfolio',
            type='button',
            name='add',
            n_clicks=0
        ),
    ],
    ),
    html.Hr(),
    html.Div([
        dash_table.DataTable(
            id='portfolio-table',
            columns=[{'name':i, 'id':i} for i in state['columns']['portfolio']],
            data=[]
        )
    ],
    id='stock-portfolio'
    ),
    html.Hr(),
    html.Div([
        dash_table.DataTable(
            id='portfolio-total',
            columns=[{'name':i, 'id':i} for i in state['columns']['total']],
            data=[]
        )
    ]),
    html.Hr(),
    html.Div([
        dcc.RadioItems(
            id='portfolio-timeline',
            options=[
                {'label': '7 Days', 'value': 7},
                {'label': '30 Days', 'value': 30},
                {'label': '60 Days', 'value': 60},
                {'label': '90 Days', 'value': 90},
                {'label': '365 Days', 'value': 365}
            ],
            value=7,
            style={
                'display': 'inline-block'
            }
        ),
        dcc.Graph(
            id='figure-total',
            figure=[]
        )
    ]),
    html.Br(),
    html.Hr(),
    html.Br(),
    html.H2(
        children='My Watchlist',
        style={
            'width': '100%'
        }
    ),
    html.Hr(),
    html.Div([
        dcc.Dropdown(
            id='watchlist-ticker',
            placeholder='Enter Stock Ticker',
            options=[{'label':i[0]+' - '+i[1], 'value':i[1]} for i in state['equity_list']],
            style={
                'width':'43%'
            }
        ),
        html.Button(
            children='Add to Watchlist',
            id='add-watchlist',
            type='button',
            name='add',
            n_clicks=0
        )
    ]),
    html.Hr(),
    html.Div([
        dash_table.DataTable(
            id='watchlist-table',
            columns=[{'name':i, 'id':i} for i in state['columns']['watchlist']],
            data=[],
            row_selectable='single',
            selected_rows=[0]
        )
    ],
    id='stock-watchlist'
    ),
    html.Hr(),
    html.Div([
        dcc.RadioItems(
            id='watchlist-timeline',
            options=[
                {'label': '7 Days', 'value': 7},
                {'label': '30 Days', 'value': 30},
                {'label': '60 Days', 'value': 60},
                {'label': '90 Days', 'value': 90},
                {'label': '365 Days', 'value': 365}
            ],
            value=7,
            style={
                'display': 'inline-block'
            }
        ),
        dcc.Graph(
            id='watchlist-figure',
            figure=[]
        )
    ])
])

# Callback to update portfolio figure and table when a new stock is added to the list
@app.callback(Output('portfolio-table', 'data'), [Input('add-portfolio', 'n_clicks')], [State('portfolio-ticker', 'value'), State('stock-price', 'value'), State('stock-shares', 'value'), State('portfolio-table', 'data')])
def addToPortfolio(clicks, ticker, price, shares, data):

    # Initial state upon load
    if clicks == 0:
        conn = psycopg2.connect(
            database = 'cuzegotk',
            user = 'cuzegotk',
            password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
            host = 'raja.db.elephantsql.com'
        )
        cur = conn.cursor()
        cur.execute('SELECT * FROM portfolio')
        portfolio_list = cur.fetchall()
        cur.close()
        conn.close()
        rows = []

        for i in portfolio_list:
            try:
                d = web.DataReader(i[0], 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
                rows.append(
                    {
                    'Ticker': i[0],
                    'Shares': i[2],
                    'Last Price': round(d['Adj Close'][len(d)-1], 2),
                    'Change(%)': round((100*(d['Adj Close'][len(d)-1] - d['Adj Close'][len(d)-2])) / d['Adj Close'][len(d)-1], 2),
                    'Book Cost': round(i[1] * i[2], 2),
                    'Market Value': round(d['Adj Close'][len(d)-1] * i[2], 2),
                    'Unrealized Gain(%)': round(100*(((d['Adj Close'][len(d)-1] * i[2]) - (i[1] * i[2])) / (i[1] * i[2])), 2),
                    'Model Prediction': i[3],
                    'Analyst Rating': i[4]
                    }
                )

            except:
                continue

        return rows

    # Update table when new stock is added
    elif (clicks > 0) & (type(ticker) == str) & (price != None) & (shares != None):
        try:
            conn = psycopg2.connect(
                database = 'cuzegotk',
                user = 'cuzegotk',
                password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
                host = 'raja.db.elephantsql.com'
            )

            cur = conn.cursor()
            cur.execute('INSERT INTO portfolio VALUES(%s, %s, %s)', (ticker.upper(), price, shares))
            cur.execute('DELETE FROM portfolio WHERE ticker is null')
            conn.commit()
            new_data = data

            d = web.DataReader(ticker, 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
            features = f.getFeatures(ticker.upper(), d)
            prediction = f.fitModel(features)
            cur.execute('UPDATE portfolio SET modelrating = %s, marketrating = %s WHERE ticker = %s', (prediction, features[0][-1], ticker.upper()))
            conn.commit()
            cur.close()
            conn.close()

            new_row = {
                'Ticker': ticker.upper(),
                'Shares': shares,
                'Last Price': round(d['Adj Close'][len(d)-1], 2),
                'Change(%)': round((100*(d['Adj Close'][len(d)-1] - d['Adj Close'][len(d)-2])) / d['Adj Close'][len(d)-1], 2),
                'Book Cost': round(shares * price, 2),
                'Market Value': round(d['Adj Close'][len(d)-1] * shares, 2),
                'Unrealized Gain(%)': round((100*((d['Adj Close'][len(d)-1] * shares) - (price * shares))) / (price * shares),2),
                'Model Prediction': prediction,
                'Analyst Rating': features[0][-1]
            }
            new_data.append(new_row)

            return new_data

        except:
            pass

# Callback to update portfolio returns table
@app.callback(Output('portfolio-total', 'data'), [Input('portfolio-table', 'data')], [State('portfolio-ticker', 'value'), State('stock-price', 'value'), State('stock-shares', 'value')])
def updateTotal(rows, ticker, price, shares):

    # Initial state upon load
    if rows == []:
        conn = psycopg2.connect(
            database = 'cuzegotk',
            user = 'cuzegotk',
            password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
            host = 'raja.db.elephantsql.com'
        )
        cur = conn.cursor()
        cur.execute('SELECT * FROM portfolio')
        portfolio_list = cur.fetchall()
        cur.close()
        conn.close()
        total = []
        book, market = (0,0)

        for i in portfolio_list:
            try:
                d = web.DataReader(i[0], 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
                book = book + round(i[1] * i[2], 2)
                market = market + round(d['Adj Close'][len(d)-1] * i[2], 2)

            except:
                continue
        if book > 0:
            return [{
                'Number of Stocks': len(portfolio_list),
                'Portfolio Book Cost': book,
                'Portfolio Market Value': market,
                'Unrealized Portfolio Gain(%)':round((100*(market - book)) / book, 2)
            }]

    # Update table when new stock is added
    else:
        total = []
        book, market = (0,0)

        for i in rows:
            book = book + round(i['Book Cost'], 2)
            market = market + round(i['Market Value'], 2)

        total.append({
            'Number of Stocks': len(rows),
            'Portfolio Book Cost': book,
            'Portfolio Market Value': market,
            'Unrealized Portfolio Gain(%)':round((100*(market - book)) / book, 2)
            })

        return total

# Callback to update portfolio returns figure
@app.callback(Output('figure-total', 'figure'), [Input('portfolio-timeline', 'value'), Input('portfolio-total', 'data')], [State('figure-total', 'figure'), State('portfolio-table', 'data')])
def updatePortfolioFigure(days, rows, fig, p_rows):

    # Initial state upon load
    if fig == []:

        conn = psycopg2.connect(
            database = 'cuzegotk',
            user = 'cuzegotk',
            password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
            host = 'raja.db.elephantsql.com'
        )
        cur = conn.cursor()
        cur.execute('SELECT * FROM portfolio')
        portfolio_list = cur.fetchall()
        cur.close()
        conn.close()

        new_figure = None
        xaxis = []
        yaxis = []
        book = 0
        try:
            d0 = web.DataReader(portfolio_list[0][0], 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
            for i in d0.index:
                xaxis.append(i)
        except:
            pass

        yaxis = np.zeros(len(xaxis))
        for i in portfolio_list:
            try:
                d = web.DataReader(i[0], 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
                book = book + round(i[1] * i[2], 2)
                yaxis = yaxis + (d['Adj Close'] * i[2]).values
            except:
                continue

        yaxis = (100*(yaxis - book) / book)

        new_figure = go.Figure(
                        data=[go.Scatter(
                            x=xaxis,
                            y=yaxis,
                            mode='lines+markers'
                        )],
            layout=go.Layout(title='Unrealized Portfolio Return: {} Days'.format(days),xaxis={'title': 'Date'},yaxis={'title': 'Cumulative Unrealized Return(%)'},hovermode='closest')
        )

        return new_figure

    # Update table when new stock is added
    else:
        new_figure = None
        xaxis = []
        yaxis = []
        book = 0
        try:
            d0 = web.DataReader(p_rows[0]['Ticker'], 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
            for i in d0.index:
                xaxis.append(i)
        except:
            pass

        yaxis = np.zeros(len(xaxis))
        for i in p_rows:
            try:
                d = web.DataReader(i['Ticker'], 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
                book = book + round(i['Book Cost'], 2)
                yaxis = yaxis + (d['Adj Close'] * i['Shares']).values
            except:
                continue

        yaxis = (100*(yaxis - book) / book)

        new_figure = go.Figure(
                        data=[go.Scatter(
                            x=xaxis,
                            y=yaxis,
                            mode='lines+markers'
                        )],
            layout=go.Layout(title='Unrealized Portfolio Return: {} Days'.format(days),xaxis={'title': 'Date'},yaxis={'title': 'Cumulative Unrealized Return(%)'},hovermode='closest')
        )

        return new_figure

# Callback to update watchlist figure and table when a new stock is added or selected
@app.callback(Output('watchlist-table', 'data'), [Input('add-watchlist', 'n_clicks')], [State('watchlist-ticker', 'value'), State('watchlist-table', 'data')])
def addToWatchlist(clicks, ticker, data):

    # Initial state upon load
    if clicks == 0:
        conn = psycopg2.connect(
            database = 'cuzegotk',
            user = 'cuzegotk',
            password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
            host = 'raja.db.elephantsql.com'
        )
        cur = conn.cursor()
        cur.execute('SELECT * FROM watchlist')
        watchlist_list = cur.fetchall()
        cur.close()
        conn.close()

        rows = []
        for i in watchlist_list:
            try:
                d = web.DataReader(i[0], 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
                rows.append(
                    {
                    'Ticker': i[0],
                    'Last Price': round(d['Adj Close'][len(d)-1], 2),
                    'Last close': round(d['Adj Close'][len(d)-2], 2),
                    'Volume': d['Volume'][len(d)-1],
                    'Change(%)': round((100*(d['Adj Close'][len(d)-1] - d['Adj Close'][len(d)-2])) / d['Adj Close'][len(d)-1], 2),
                    'Model Prediction': i[1],
                    'Analyst Rating': i[2]
                    }
                )
            except:
                continue

        return rows

    # Update table when new stock is selected
    if clicks > 0 and type(ticker) == str:
        try:
            conn = psycopg2.connect(
                database = 'cuzegotk',
                user = 'cuzegotk',
                password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
                host = 'raja.db.elephantsql.com'
            )
            cur = conn.cursor()
            cur.execute('INSERT INTO watchlist VALUES(%s)', [ticker.upper()])
            cur.execute('DELETE FROM watchlist WHERE ticker is null')
            conn.commit()
            new_data = data

            d = web.DataReader(ticker, 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
            features = f.getFeatures(ticker.upper(), d)
            prediction = f.fitModel(features)
            cur.execute('UPDATE watchlist SET modelrating = %s, marketrating = %s WHERE ticker = %s', (prediction, features[0][-1], ticker.upper()))
            conn.commit()
            cur.close()
            conn.close()
            new_row = {
                'Ticker': ticker.upper(),
                'Last Price': round(d['Adj Close'][len(d)-1], 2),
                'Last close': round(d['Adj Close'][len(d)-2], 2),
                'Volume': d['Volume'][len(d)-1],
                'Change(%)': round((100*(d['Adj Close'][len(d)-1] - d['Adj Close'][len(d)-2])) / d['Adj Close'][len(d)-1], 2),
                'Model Prediction': prediction,
                'Analyst Rating': features[0][-1]
            }
            new_data.append(new_row)

            return new_data

        except:
            pass

# Update stock chart figure when new stock is added to the watchlist
@app.callback(Output('watchlist-figure', 'figure'), [Input('watchlist-timeline', 'value'), Input('watchlist-table', 'selected_rows')], [State('watchlist-figure', 'figure'), State('watchlist-table', 'data')])
def updateWatchlistFigure(days, selected_row, fig, data):

    # Initial State upon load
    if fig == []:
        conn = psycopg2.connect(
            database = 'cuzegotk',
            user = 'cuzegotk',
            password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
            host = 'raja.db.elephantsql.com'
        )
        cur = conn.cursor()
        cur.execute('SELECT * FROM watchlist')
        ind = selected_row[0]
        query = cur.fetchall()[ind][0]
        cur.close()
        conn.close()
        xaxis = []
        yaxis = []
        try:
            d0 = web.DataReader(query, 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
            for i,date in enumerate(d0.index):
                xaxis.append(date)
                yaxis.append(d0['Adj Close'][i])
        except:
            pass

        new_figure = go.Figure(
                        data=[go.Scatter(
                            x=xaxis,
                            y=yaxis,
                            name=query,
                            mode='lines+markers'
                        )],
            layout=go.Layout(title='{} Price Chart: {} Days'.format(query, days),xaxis={'title': 'Date'},yaxis={'title': 'Stock Price'},hovermode='closest')
        )

        return new_figure

    # Update figure when new stock is selected
    else:
        ind = selected_row[0]
        selected = data[ind]['Ticker']
        xaxis = []
        yaxis = []
        try:
            d0 = web.DataReader(selected, 'yahoo', (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'))
            for i,date in enumerate(d0.index):
                xaxis.append(date)
                yaxis.append(d0['Adj Close'][i])

        except:
            pass

        new_figure = go.Figure(
                        data=[go.Scatter(
                            x=xaxis,
                            y=yaxis,
                            name=selected,
                            mode='lines+markers'
                        )],
            layout=go.Layout(title='{} Price Chart: {} Days'.format(selected, days),xaxis={'title': 'Date'},yaxis={'title': 'Stock Price'},hovermode='closest')
        )

        return new_figure

if __name__ == '__main__':
    app.run_server()
