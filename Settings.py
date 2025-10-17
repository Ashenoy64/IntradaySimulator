import os

SIMULATION_RESULTS_PATH = 'simulation_results'
MODELS_STORE_PATH='models'
DATA_STORE_PATH='simulation_results'
FORMAT_DATA_PATH='formatted_data'
SCALER_PATH='models/scaler'

dirs = [
    SIMULATION_RESULTS_PATH,
    MODELS_STORE_PATH,
    FORMAT_DATA_PATH
]

for dir in dirs:
    os.makedirs(dir,exist_ok=True)