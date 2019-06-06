import numpy as np
import pandas as pd
import psycopg2
import pickle

# Connect to database
conn = psycopg2.connect(
    database = 'cuzegotk',
    user = 'cuzegotk',
    password = 'NekW2BqJ8hW1wO3hCdpuEESPiP-y131V',
    host = 'raja.db.elephantsql.com'
)
cur = conn.cursor()
# Query list of features
cur.execute('SELECT * FROM features')
features = cur.fetchall()
cur.close()
conn.close()

# Clean and unwrangle data
columns = ['ticker', 'sector', 'weeklyma', 'monthlyma', 'yearlyma', 'gross/revenue', 'gross/revenue-1yr', 'gross/revenue-2yr', 'net/revenue', 'net/revenue-1yr', 'net/revenue-2yr', 'current-ratio', 'debt-equity', 'debt-asset', 'rating']
df = pd.DataFrame(data = features, columns = columns)
df.set_index('ticker', inplace=True)
df.dropna(inplace=True)
df = df[df['sector'] != 'NaN']

# Set X and Y values to train and fit logistic regression one vs. all model
X = df.iloc[:,:-1]
Y = df.iloc[:,-1]
X_encode = pd.get_dummies(X.iloc[:,0])
Y_encode = pd.get_dummies(Y)
X = pd.concat([X_encode, X.drop(columns=['sector'])], axis=1, join_axes=[X_encode.index])

# Training and Test set split 80/20
from sklearn.model_selection import train_test_split
y = Y_encode.values
x = X.values
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, stratify=y)

from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

# Fit and train model using training set
model = OneVsRestClassifier(LogisticRegression(solver='liblinear', multi_class='ovr')) # 'lbfgs' , 'liblinear'
model.fit(x_train, y_train)
# Predict using trained model
y_prob = model.predict_proba(x_test)

# Pickle model
filename = 'model.pkl'
outfile = open(filename, 'wb')
pickle.dump(model, outfile)
outfile.close()

# Map labels based on probability
labels = Y_encode.columns
y_pred = []
y_true = []

for i in y_prob:
    y_pred.append(labels[i.argmax()])

for i in y_test:
    y_true.append(labels[i.argmax()])

# Error Analysis
from sklearn.metrics import classification_report, accuracy_score
print(classification_report(y_true, y_pred))
print(round(accuracy_score(y_true, y_pred),2))
