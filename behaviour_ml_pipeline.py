import joblib
import os

from sklearn.ensemble import IsolationForest


class BehaviourModel:

    def __init__(self):

        self.model = None

        self.model_path = "behaviour_model.pkl"

    # -----------------------------
    # Train Model
    # -----------------------------

    def train(self, data):

        self.model = IsolationForest(

            n_estimators=100,
            contamination=0.1,
            random_state=42

        )

        self.model.fit(data)

        self.save()

    # -----------------------------
    # Save Model
    # -----------------------------

    def save(self):

        joblib.dump(self.model, self.model_path)

    # -----------------------------
    # Load Model
    # -----------------------------

    def load(self):

        if not os.path.exists(self.model_path):
            raise Exception("Model not found")

        self.model = joblib.load(self.model_path)

    # -----------------------------
    # Predict Behaviour
    # -----------------------------

    def predict(self, features):

        if self.model is None:
            return "unknown"

        result = self.model.predict([features])[0]

        if result == 1:
            return "normal"

        return "anomaly"