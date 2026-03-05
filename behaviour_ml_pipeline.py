import numpy as np
from sklearn.ensemble import IsolationForest
import pickle

# ===============================
# Behaviour ML Model Class
# ===============================

class BehaviourModel:

    def __init__(self):

        # Anomaly detection model
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )

        self.trained = False


    # ---------------------------
    # Training Function
    # ---------------------------

    def train(self, X):

        """
        X → numpy array of behaviour feature vectors
        """

        self.model.fit(X)
        self.trained = True


    # ---------------------------
    # Prediction Function
    # ---------------------------

    def predict(self, feature_vector):

        if not self.trained:
            return "model_not_trained"

        feature_vector = np.array(feature_vector).reshape(1, -1)

        result = self.model.predict(feature_vector)

        if result[0] == -1:
            return "intruder"

        return "normal"


    # ---------------------------
    # Save Model
    # ---------------------------

    def save(self, path="behaviour_model.pkl"):

        with open(path, "wb") as f:
            pickle.dump(self.model, f)


    # ---------------------------
    # Load Model
    # ---------------------------

    def load(self, path="behaviour_model.pkl"):

        with open(path, "rb") as f:
            self.model = pickle.load(f)

        self.trained = True