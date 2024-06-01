import os

from flask import jsonify, Blueprint
import joblib
from flask import request
from app.infrastructure.ConnectDB import db, get_shared_connection
from sklearn.preprocessing import StandardScaler

import pandas as pd
import numpy as np
from flask_cors import CORS
from sklearn.preprocessing import MinMaxScaler
from flask import Flask, jsonify
from sklearn.model_selection import GridSearchCV
from scikeras.wrappers import KerasRegressor

from keras.models import Sequential
from keras.layers import LSTM, Dense
from sqlalchemy import func, desc, text
from flask import jsonify
from sqlalchemy import text

from app.models.PRIHST import Prihst
from app.portfolio.FundDetails import api_getALLPrices_blueprint

api_predictPrices_blueprint = Blueprint('api_predict_prices', __name__)

api_createModel_blueprint = Blueprint('api_create_model', __name__)
CORS(api_createModel_blueprint)

api_highest_prices_blueprint = Blueprint('api_highest_prices', __name__)
CORS(api_highest_prices_blueprint)

api_createUseModel_blueprint = Blueprint('api_createUseModel', __name__)
CORS(api_createUseModel_blueprint)

from keras.models import load_model as keras_load_model


def load_model(model_path):
    try:
        model = keras_load_model(model_path)
        return model
    except Exception as e:
        print(f"Error loading the PricePrediction: {e}")
        return None


def order_prices_chronologically(prices_data_list):
    try:
        df = pd.DataFrame(prices_data_list)

        df['prcdate'] = pd.to_datetime(df['prcdate'])

        # Order prices chronologically based on the timestamp
        ordered_df = df.sort_values(by='prcdate')
        print("prices ordered chrono")
        return ordered_df

    except Exception as e:
        print(f"Error in order_prices_chronologically: {str(e)}")
        raise


def handle_null_values(dataframe):
    # Example: Drop rows with null values
    cleaned_df = dataframe.dropna()
    print("null values handled")
    return cleaned_df


def scale_data(dataset):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)
    print("data scaled")

    return scaled_data, scaler


def create_sequences(data, sequence_length=80):
    x_data, y_data = [], []

    for i in range(sequence_length, len(data)):
        x_data.append(data[i - sequence_length:i, 0])
        y_data.append(data[i, 0])

    x_data, y_data = np.array(x_data), np.array(y_data)
    print("sequences created")

    return x_data, y_data


def pre_processData(prices_data_list):
    try:
        # Step 1: Order prices chronologically
        ordered_df = order_prices_chronologically(prices_data_list)

        # Step 2: Check for null values in the DataFrame and handle them
        cleaned_df = handle_null_values(ordered_df)

        # Step 3: Select important features and prepare data for LSTM model
        data = cleaned_df[["prcdate", "price"]].rename(columns={"prcdate": "ds", "price": "y"})
        data_prices = data.filter(['y'])
        dataset = data_prices.values

        # Step 4: Scale the data
        scaled_data, scaler = scale_data(dataset)

        # Step 5: Create sequences for training the LSTM model
        x_train, y_train = create_sequences(scaled_data)
        print("Split the data into training and test sets")
        x_data, y_data = create_sequences(scaled_data)

        # Step 6: Split the data into training and test sets
        training_data_len = int(np.ceil(len(dataset) * 0.95))
        x_train, y_train = x_data[:training_data_len], y_data[:training_data_len]
        x_test, y_test = x_data[training_data_len:], y_data[training_data_len:]

        return x_train, y_train, x_test, y_test

    except Exception as e:
        print(f"Error in pre_processData: {str(e)}")
        raise


def create_lstm_model(x_train):
    print("Enter create lstm model")

    model = Sequential()
    model.add(LSTM(128, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dense(25, activation='relu'))
    model.add(Dense(1, activation='linear'))
    model.compile(optimizer='adam', loss='mean_squared_error')

    return model


def train_lstm_model(x_train, y_train, batch_size=32, epochs=10):
    try:
        # Use lambda function to pass parameters to create_lstm_model
        lstm_model = KerasRegressor(build_fn=lambda: create_lstm_model(x_train), epochs=epochs, batch_size=batch_size,
                                    verbose=1)

        param_grid_lstm = {
            'batch_size': [16, 32, 64],
            'epochs': [8, 16, 32],
            'optimizer': ['adam']
        }

        print('enter grid search')

        gridsearch_lstm = GridSearchCV(estimator=lstm_model, param_grid=param_grid_lstm, cv=3,
                                       scoring='neg_mean_squared_error', n_jobs=-1, error_score=0)
        print('enter grid search fit')

        grid_result_lstm = gridsearch_lstm.fit(x_train, y_train)
        print('grid_result_lstm :', grid_result_lstm)
        # Get the best hyperparameters
        best_batch_size = grid_result_lstm.best_params_['batch_size']
        print('best batch size: ', best_batch_size)
        best_epochs = grid_result_lstm.best_params_['epochs']
        print(' best_epochs: ', best_epochs)

        best_optimizer = grid_result_lstm.best_params_['optimizer']
        print('enter final model create')

        # Train the final model with the best hyperparameters
        final_model = create_lstm_model(x_train)

        print('enter final model fit')
        print('best_batch_size :', best_batch_size, 'best_epochs : ', best_epochs)
        final_model.fit(x_train, y_train, batch_size=best_batch_size, epochs=best_epochs, validation_split=0.2)

        return final_model

    except Exception as e:
        print(f"Error in train_lstm_model: {str(e)}")
        return None


def train_and_save_model(ticker, prices_data_list):
    try:
        # Preprocess the data
        x_train, y_train, x_test, y_test = pre_processData(prices_data_list)
        print("Sequences created. Shapes: x_train =", x_train.shape, ", y_train =", y_train.shape)

        # Train the final model
        final_model = train_lstm_model(x_train, y_train)

        if final_model:
            # Save the trained model with the ticker as part of the file name
            model_filename = f'D:/Project/{ticker}.h5'
            final_model.save(model_filename)

            return model_filename  # Return the saved model filename

        else:
            return None

    except Exception as e:
        print(f"Error in train_and_save_model: {str(e)}")
        return None


@api_createModel_blueprint.route('/getModel', methods=['POST'])
def create_model():
    try:
        # Assuming you send the prices_data_list as a JSON in the request body
        request_data = request.get_json()
        prices_data_list = request_data.get('data')

        if not prices_data_list:
            return jsonify({'error': 'Failed to retrieve pricing data'}), 500

        # Extract fund and ticker from the first entry in prices_data_list
        if prices_data_list:
            fund = prices_data_list[0].get('fund')
            tkr = prices_data_list[0].get('tkr')
            print("we got the prices")
        else:
            return jsonify({'error': 'Invalid pricing data format'}), 400

        print('prices_data_list', prices_data_list)

        # Check if the model file already exists
        model_filename = f'D:/Project/{tkr}.h5'
        if os.path.exists(model_filename):
            print('before load model')
            # Load the existing model
            model = load_model(model_filename)
            print('model loaded')
            last_data_point = prices_data_list[-1]
            print('last_data_point', last_data_point)
            print('before data prices')
            data_prices_list = []
            for record in prices_data_list:
                price_value = record.get('price')
                if price_value is not None:
                    data_prices_list.append(price_value)
            print('after data prices')
            # Convert the list to a numpy array (assuming it's needed later in your code)
            dataset = np.array(data_prices_list)
            print('dataset', dataset)
            dataset = dataset.reshape(-1, 1)

            training_data_len = int(np.ceil(len(dataset) * .95))

            print('training_data_len', training_data_len)
            scaler = MinMaxScaler(feature_range=(0, 1))
            print('before scaler')
            scaled_data = scaler.fit_transform(dataset)
            print('scaled_data')

            test_data = scaled_data[training_data_len - 80:, :]
            print('test_data')

            time_step = 80
            x_input = test_data[len(test_data) - time_step:].reshape(1, -1)
            temp_input = list(x_input)
            temp_input = temp_input[0].tolist()

            from numpy import array

            lst_output = []
            n_steps = time_step
            i = 0
            pred_days = 2
            while (i < pred_days):

                if (len(temp_input) > time_step):

                    x_input = np.array(temp_input[1:])
                    # print("{} day input {}".format(i,x_input))
                    x_input = x_input.reshape(1, -1)
                    x_input = x_input.reshape((1, n_steps, 1))

                    yhat = model.predict(x_input, verbose=0)
                    # print("{} day output {}".format(i,yhat))
                    temp_input.extend(yhat[0].tolist())
                    temp_input = temp_input[1:]

                    lst_output.extend(yhat.tolist())
                    i = i + 1

                else:

                    x_input = x_input.reshape((1, n_steps, 1))
                    yhat = model.predict(x_input, verbose=0)
                    temp_input.extend(yhat[0].tolist())

                    lst_output.extend(yhat.tolist())
                    i = i + 1

            print("Output of predicted next days: ", (lst_output))

            if model is None:
                print('model is none')
                return jsonify({'error': f'Failed to load the existing model for {tkr}'}), 500
            else:
                print('model loaded')

                return jsonify({'Model Loading': f'Existing model for {tkr} loaded correctly'}), 200
        else:
            # Train and save the model

            model_filename = train_and_save_model(tkr, prices_data_list)

            if model_filename:
                return jsonify({'success': f'Model for {tkr} created and saved as {model_filename}'}), 200
            else:
                return jsonify({'error': 'Failed to create and save the model'}), 500

    except Exception as e:
        print(f"Error predicting next day's price: {e}")
        return jsonify({'error': f'Failed to predict next day\'s price. Exception: {str(e)}'}), 500


@api_highest_prices_blueprint.route('/highestPriceChange', methods=['GET'])
def get_highest_price_change():
    try:
        connection = get_shared_connection()

        query = text("""
           SELECT TKR,
       PRICE - LAG(PRICE) OVER (PARTITION BY TKR ORDER BY PRCDATE) AS price_change
FROM PRIHST
WHERE TKR IS NOT NULL
and FUND='504'
  AND EXTRACT(YEAR FROM PRCDATE) = 2024
ORDER BY TKR, PRCDATE DESC
        """)

        result = connection.execute(query)

        # Fetch the result
        rows = result.fetchall()
        print('rows', rows)
        if not rows:
            return jsonify({'error': 'No data found'}), 404

        # Find the ticker with the highest price change
        max_change_ticker = max(rows, key=lambda x: x[1] if x[1] is not None else 0)
        print('max_change_ticker', max_change_ticker)

        tkr, highest_change = max_change_ticker[0], max_change_ticker[1]
        print(tkr, highest_change)

        query = text("""
                   SELECT TKR,PRCDATE,PRICE
                   FROM PRIHST
                   WHERE TKR = :tkr
                    and PRCDATE >= TO_DATE('01/01/2023', 'MM/DD/YYYY') order by PRCDATE 
               """)
        prices = connection.execute(query.params(tkr=tkr))

        fund_data = prices.fetchall()

        # Check if there is any data
        if not fund_data:
            return jsonify({'error': 'No data found'}), 404

        prihstdata_list = [dict(row._asdict()) for row in fund_data]

        return jsonify(
            {'highest_change_ticker': tkr, 'highest_change': highest_change, 'prihstdata_list': prihstdata_list})

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in get_highest_price_change: {str(e)}")
        return jsonify({'error': str(e)}), 500


import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from keras.utils import to_categorical
import math

def calculate_percentage_error(actual, predicted):
    error = np.abs(actual - predicted) / np.abs(actual)
    percentage_error = np.mean(error) * 100
    return percentage_error

def trainlstm_model(df, batch_size=4, epochs=32, optimizer='adam'):
    shape = df.shape[0]
    df_new = df[['price']]
    dataset = df_new.values
    train = df_new[:int(shape * 0.75)]
    valid = df_new[int(shape * 0.75):]

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)

    x_train, y_train = [], []
    for i in range(40, len(train)):
        x_train.append(scaled_data[i - 40:i, 0])
        y_train.append(scaled_data[i, 0])

    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(units=50))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer=optimizer)

    model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=2)

    return model, scaler, scaled_data

def predict_next_period_prices(df, model, scaler, scaled_data, time_step=40, pred_days=40):
    # Prepare the test data
    data = df[["prcdate", "price"]]  # Select Date and Price
    data = data.rename(columns={"prcdate": "ds", "price": "y"})  # Renaming the columns of the dataset

    data_prices = data.filter(['y'])
    dataset = data_prices.values

    training_data_len = int(np.ceil(len(dataset) * .95))

    test_data = scaled_data[training_data_len - time_step:, :]

    # Reshape the input for prediction
    x_input = test_data[len(test_data) - time_step:].reshape(1, -1)
    temp_input = list(x_input)
    temp_input = temp_input[0].tolist()

    # Generate predictions for the next pred_days
    lst_output = []
    i = 0

    while i < pred_days:
        if len(temp_input) > time_step:
            x_input = np.array(temp_input[1:])
            x_input = x_input.reshape(1, -1)
            x_input = x_input.reshape((1, time_step, 1))

            yhat = model.predict(x_input, verbose=0)
            temp_input.extend(yhat[0].tolist())
            temp_input = temp_input[1:]

            lst_output.extend(yhat.tolist())
            i += 1
        else:
            x_input = np.array(temp_input).reshape((1, time_step, 1))
            yhat = model.predict(x_input, verbose=0)
            temp_input.extend(yhat[0].tolist())

            lst_output.extend(yhat.tolist())
            i += 1

    # Inverse transform the predictions to get actual prices
    predicted_prices = scaler.inverse_transform(np.array(lst_output).reshape(-1, 1))

    return predicted_prices


@api_createUseModel_blueprint.route('/CreateUse/<string:tkr>', methods=['POST'])
def CreateUsemodel(tkr):
    try:
        # Extract JSON data from the POST request
        json_data = request.get_json()

        # Convert JSON data to DataFrame
        df_prihst = pd.DataFrame(json_data)

        # Check if the DataFrame is not empty
        if df_prihst.empty:
            return jsonify({"error": "Empty DataFrame received"}), 400

        ticker = tkr

        # Check if the model file already exists
        model_filename = f'D:/Project/{ticker}.h5'
        if os.path.exists(model_filename):
            # Load the existing model
            model = load_model(model_filename)
            shape = df_prihst.shape[0]
            df_new = df_prihst[['price']]
            dataset = df_new.values
            train = df_new[:int(shape * 0.75)]
            valid = df_new[int(shape * 0.75):]

            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(dataset)

            print('after load model')

        else:
            print('Creade  model')
            model, scaler, scaled_data = trainlstm_model(df_prihst, batch_size=4, epochs=32, optimizer='adam')

        if model:
            # Save the trained model with the ticker as part of the file name
            model_filename = f'D:/Project/{ticker}.h5'
            model.save(model_filename)

        predicted_prices = predict_next_period_prices(df_prihst, model, scaler, scaled_data, time_step=40, pred_days=68)

        # Return the predicted prices
        return jsonify(predicted_prices.tolist()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
