import csv
import os


class BehaviourDataset:

    def __init__(self):

        self.dataset_file = "behaviour_data.csv"

        if not os.path.exists(self.dataset_file):

            with open(self.dataset_file, "w", newline="") as f:

                writer = csv.writer(f)

                writer.writerow([
                    "typing_speed",
                    "key_delay",
                    "mouse_speed",
                    "mouse_click_rate",
                    "session_time"
                ])

    # -----------------------------
    # Add New Behaviour Sample
    # -----------------------------

    def add_sample(self, features):

        with open(self.dataset_file, "a", newline="") as f:

            writer = csv.writer(f)

            writer.writerow(features)

    # -----------------------------
    # Load Dataset
    # -----------------------------

    def load(self):

        data = []

        with open(self.dataset_file, "r") as f:

            reader = csv.reader(f)

            next(reader)

            for row in reader:
                data.append([float(x) for x in row])

        return data