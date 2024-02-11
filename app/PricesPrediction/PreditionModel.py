from flask import jsonify, Blueprint
import joblib
from flask import request

import pandas as pd
import numpy as np
from flask_cors import CORS
from sklearn.preprocessing import MinMaxScaler
from flask import Flask, jsonify
from sklearn.model_selection import GridSearchCV
from scikeras.wrappers import KerasRegressor

from keras.models import Sequential
from keras.layers import LSTM, Dense

from app.portfolio.FundDetails import api_getALLPrices_blueprint

api_predictPrices_blueprint = Blueprint('api_predict_prices', __name__)

api_createModel_blueprint = Blueprint('api_create_model', __name__)
CORS(api_createModel_blueprint)


def load_model(model_path):
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        print(f"Error loading the PricePrediction: {e}")
        return None

@api_predictPrices_blueprint.route('/predictPrices', methods=['GET'])
def predict_next_day_price():
    try:
        model_path = 'D:/Project/best_model.pkl'
        model = load_model(model_path)

        if model is None:
            return jsonify({'error': 'Failed to load the PricePrediction'}), 500
        else:
            return jsonify({'Model Loading': 'Model loaded correcrly'}), 200

    except Exception as e:
        print(f"Error predicting next day's price: {e}")
        return jsonify({'error': f'Failed to predict next day\'s price. Exception: {str(e)}'}), 500




def order_prices_chronologically(prices_data_list):
    """
    Order prices chronologically based on the timestamp.

    Parameters:
    - prices_data_list: list
      The list of dictionaries representing pricing data.

    Returns:
    - ordered_df: pandas DataFrame
      The DataFrame with prices ordered chronologically.
    """
    try:
        # Convert list of dictionaries to DataFrame
        df = pd.DataFrame(prices_data_list)

        # Ensure that the timestamp column is in datetime format
        df['prcdate'] = pd.to_datetime(df['prcdate'])

        # Order prices chronologically based on the timestamp
        ordered_df = df.sort_values(by='prcdate')
        print("prices ordered chrono")
        return ordered_df

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in order_prices_chronologically: {str(e)}")
        raise  # You might want to handle or log the exception based on your application's needs

def handle_null_values(dataframe):
    """
    Handle null values in the DataFrame.

    Parameters:
    - dataframe: pandas DataFrame
      The input DataFrame.

    Returns:
    - cleaned_df: pandas DataFrame
      The DataFrame with null values handled.
    """
    # Example: Drop rows with null values
    cleaned_df = dataframe.dropna()
    print("null values handled")
    return cleaned_df

def scale_data(dataset):
    """
    Scale the input dataset using Min-Max scaling.

    Parameters:
    - dataset: numpy array
      The input data.

    Returns:
    - scaled_data: numpy array
      The scaled data.
    - scaler: sklearn.preprocessing.MinMaxScaler
      The scaler object fitted on the data.
    """
    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_data = scaler.fit_transform(dataset)
    print("data scaled")

    return scaled_data, scaler

def create_sequences(data, sequence_length=80):
    """
    Create input sequences for LSTM model.

    Parameters:
    - data: numpy array
      The input data.
    - sequence_length: int, optional (default=80)
      The length of input sequences.

    Returns:
    - x_data: numpy array
      The input sequences.
    - y_data: numpy array
      The target values.
    """
    x_data, y_data = [], []

    for i in range(sequence_length, len(data)):
        x_data.append(data[i-sequence_length:i, 0])
        y_data.append(data[i, 0])

    x_data, y_data = np.array(x_data), np.array(y_data)
    print("sequences created")

    return x_data, y_data

def pre_processData(prices_data_list):
    """
    Preprocess the data obtained from the Flask API endpoint.

    Parameters:
    - prices_data_list: list
      The list of dictionaries representing pricing data obtained from the API.

    Returns:
    - train_data: numpy array
      The training data.
    - test_data: numpy array
      The test data.
    """
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
        lstm_model = KerasRegressor(build_fn=lambda: create_lstm_model(x_train), epochs=epochs, batch_size=batch_size, verbose=0)

        param_grid_lstm = {
            'batch_size': [16, 32, 64],
            'epochs': [8, 16, 32],
            'optimizer': ['adam']
        }

        print('enter grid search')

        gridsearch_lstm = GridSearchCV(estimator=lstm_model, param_grid=param_grid_lstm, cv=3, scoring='neg_mean_squared_error', n_jobs=-1, error_score=0)
        print('enter grid search fit')

        grid_result_lstm = gridsearch_lstm.fit(x_train, y_train)

        # Get the best hyperparameters
        best_batch_size = grid_result_lstm.best_params_['batch_size']
        best_epochs = grid_result_lstm.best_params_['epochs']
        best_optimizer = grid_result_lstm.best_params_['optimizer']
        print('enter final model create')

        # Train the final model with the best hyperparameters
        final_model = create_lstm_model(x_train)

        print('enter final model fit')

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

        # Train and save the model
        model_filename = train_and_save_model(tkr, prices_data_list)

        if model_filename:
            return jsonify({'success': f'Model for {tkr} created and saved as {model_filename}'}), 200
        else:
            return jsonify({'error': 'Failed to create and save the model'}), 500

    except Exception as e:
        print(f"Error creating and saving the model: {e}")
        return jsonify({'error': f'Failed to create and save the model. Exception: {str(e)}'}), 500
