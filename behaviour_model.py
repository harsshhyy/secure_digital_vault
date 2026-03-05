import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

MODEL_FILE = "behaviour_model.pkl"


def train_model(data):
    model = IsolationForest(contamination=0.1)

    model.fit(data)

    joblib.dump(model, MODEL_FILE)


def load_model():
    return joblib.load(MODEL_FILE)


def predict(data):
    model = load_model()
    result = model.predict([data])

    return result[0]