import csv
import random

file = "behaviour_data.csv"

samples = 2000

with open(file, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "typing_speed",
        "key_delay",
        "mouse_speed",
        "mouse_click_rate",
        "session_time"
    ])

    for _ in range(samples):

        typing_speed = random.uniform(3, 8)        # keys/sec
        key_delay = random.uniform(0.05, 0.25)     # seconds
        mouse_speed = random.uniform(200, 1200)    # px/sec
        mouse_click_rate = random.uniform(0.5, 3)  # clicks/sec
        session_time = random.uniform(20, 300)     # seconds

        writer.writerow([
            typing_speed,
            key_delay,
            mouse_speed,
            mouse_click_rate,
            session_time
        ])

print("Dataset generated with", samples, "samples")