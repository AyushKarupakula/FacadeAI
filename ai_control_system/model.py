import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def create_model(input_shape):
    model = models.Sequential([
        layers.Dense(64, activation='relu', input_shape=input_shape),
        layers.Dense(32, activation='relu'),
        layers.Dense(16, activation='relu'),
        layers.Dense(3, activation='linear')  # 3 outputs for façade adjustments
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def preprocess_data(data):
    # Convert weather condition to numerical
    weather_mapping = {'Clear': 0, 'Clouds': 1, 'Rain': 2, 'Snow': 3}
    data['weather_condition'] = data['weather_condition'].map(weather_mapping)
    
    # Normalize numerical columns
    scaler = StandardScaler()
    numerical_columns = ['temperature', 'humidity', 'wind_speed', 'wind_direction', 'cloudiness']
    data[numerical_columns] = scaler.fit_transform(data[numerical_columns])
    
    return data, scaler

def train_model(data_path):
    # Load and preprocess data
    data = pd.read_csv(data_path)
    data, scaler = preprocess_data(data)
    
    # For this example, we'll use dummy target values
    # In a real scenario, these would be the optimal façade adjustments
    data['target_1'] = np.random.rand(len(data))
    data['target_2'] = np.random.rand(len(data))
    data['target_3'] = np.random.rand(len(data))
    
    # Split features and targets
    features = ['temperature', 'humidity', 'wind_speed', 'wind_direction', 'cloudiness', 'weather_condition']
    targets = ['target_1', 'target_2', 'target_3']
    
    X = data[features]
    y = data[targets]
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train the model
    model = create_model((len(features),))
    model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2, verbose=1)
    
    # Evaluate the model
    loss = model.evaluate(X_test, y_test)
    print(f"Test loss: {loss}")
    
    return model, scaler

if __name__ == "__main__":
    data_path = "data_acquisition/data/processed/New_York_20230501.csv"  # Update this path
    model, scaler = train_model(data_path)
    
    # Save the model and scaler
    model.save("ai_control_system/models/facade_control_model.h5")
    import joblib
    joblib.dump(scaler, "ai_control_system/models/scaler.pkl")
