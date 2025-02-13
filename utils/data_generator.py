import json
import os
from datetime import datetime, timedelta
import random
import numpy as np

def generate_battery_data(start_date, end_date):
    current_date = start_date
    data = {}
    
    while current_date <= end_date:
        month_key = current_date.strftime("%Y-%m")
        if month_key not in data:
            data[month_key] = []
            
        # Simulate battery degradation
        days_since_start = (current_date - start_date).days
        degradation = 1 - (days_since_start * 0.00015)  # ~5% annual degradation
        
        # Generate daily data
        entry = {
            "date": current_date.strftime("%Y-%m-%d"),
            "voltage": round(48.0 * degradation + random.uniform(-0.5, 0.5), 2),
            "current": round(12.0 * degradation + random.uniform(-0.3, 0.3), 2),
            "temperature": random.randint(20 + int(days_since_start/30), 35 + int(days_since_start/30)),
            "state_of_charge": random.randint(40, 100),
            "cycles": int(days_since_start / 3),
            "capacity_ah": 100.0 * degradation,
            "internal_resistance": 0.1 * (1 + days_since_start * 0.0002)
        }
        
        data[month_key].append(entry)
        current_date += timedelta(days=1)
    
    return data

def save_data(data, base_path="data"):
    for month_key, entries in data.items():
        year, month = month_key.split('-')
        quarter = f"Q{(int(month)-1)//3 + 1}"
        
        dir_path = os.path.join(base_path, year, quarter)
        os.makedirs(dir_path, exist_ok=True)
        
        file_path = os.path.join(dir_path, f"{month}.json")
        with open(file_path, 'w') as f:
            json.dump(entries, f, indent=2)

def generate_metadata():
    metadata = {
        "battery_specs": {
            "chemistry": "LiFePO4",
            "nominal_capacity": "100Ah",
            "voltage_range": "40-58V",
            "max_temperature": 60,
            "manufacture_date": "2023-01-01"
        },
        "data_ranges": {
            "start_date": "2023-01-01",
            "end_date": "2024-12-31"
        }
    }
    
    with open('data/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    data = generate_battery_data(start_date, end_date)
    save_data(data)
    generate_metadata()