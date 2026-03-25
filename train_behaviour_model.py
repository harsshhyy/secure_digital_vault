from behaviour_dataset import BehaviourDataset
from behaviour_ml_pipeline import BehaviourModel


print("Loading dataset...")

dataset = BehaviourDataset()

data = dataset.load()

print("Samples loaded:", len(data))


print("Training behaviour model...")

model = BehaviourModel()

model.train(data)

print("Model training completed")

print("Model saved as behaviour_model.pkl")