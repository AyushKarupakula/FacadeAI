import tensorflow as tf
import numpy as np
import joblib
from data_acquisition.fetch_data import fetch_weather_data, load_config

def load_model_and_scaler():
    model = tf.keras.models.load_model("ai_control_system/models/facade_control_model.h5")
    scaler = joblib.load("ai_control_system/models/scaler.pkl")
    return model, scaler

def preprocess_input(weather_data, scaler):
    input_data = np.array([
        weather_data['main']['temp'],
        weather_data['main']['humidity'],
        weather_data['wind']['speed'],
        weather_data['wind']['deg'],
        weather_data['clouds']['all'],
        0  # placeholder for weather condition
    ]).reshape(1, -1)
    
    # Map weather condition
    weather_mapping = {'Clear': 0, 'Clouds': 1, 'Rain': 2, 'Snow': 3}
    input_data[0, 5] = weather_mapping.get(weather_data['weather'][0]['main'], 0)
    
    # Normalize the input data
    input_data[:, :5] = scaler.transform(input_data[:, :5])
    
    return input_data

def get_facade_adjustments(weather_data):
    model, scaler = load_model_and_scaler()
    input_data = preprocess_input(weather_data, scaler)
    predictions = model.predict(input_data)
    return predictions[0]

if __name__ == "__main__":
    config = load_config()
    api_key = config['openweathermap_api_key']
    city = config['city']
    
    weather_data = fetch_weather_data(api_key, city)
    adjustments = get_facade_adjustments(weather_data)
    
    print(f"Current weather in {city}:")
    print(f"Temperature: {weather_data['main']['temp']}°C")
    print(f"Humidity: {weather_data['main']['humidity']}%")
    print(f"Wind: {weather_data['wind']['speed']} m/s, {weather_data['wind']['deg']}°")
    print(f"Cloudiness: {weather_data['clouds']['all']}%")
    print(f"Condition: {weather_data['weather'][0]['main']}")
    print("\nRecommended façade adjustments:")
    print(f"Adjustment 1: {adjustments[0]:.2f}")
    print(f"Adjustment 2: {adjustments[1]:.2f}")
    print(f"Adjustment 3: {adjustments[2]:.2f}")
