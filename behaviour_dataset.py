import numpy as np
import os
import pickle

DATA_FILE = "behaviour_data.pkl"


class BehaviourDataset:

    def __init__(self):

        if os.path.exists(DATA_FILE):

            with open(DATA_FILE, "rb") as f:
                self.data = pickle.load(f)

        else:
            self.data = []


    # -----------------------------
    # Add Feature Sample
    # -----------------------------

    def add_sample(self, feature_vector):

        self.data.append(feature_vector)

        self.save()


    # -----------------------------
    # Save Dataset
    # -----------------------------

    def save(self):

        with open(DATA_FILE, "wb") as f:
            pickle.dump(self.data, f)


    # -----------------------------
    # Load Dataset
    # -----------------------------

    def get_dataset(self):

        return np.array(self.data)