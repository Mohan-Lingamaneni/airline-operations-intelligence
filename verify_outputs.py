import pandas as pd
ops = pd.read_csv('data/processed/flights_operations_2025_01.csv')
delay = pd.read_csv('data/processed/flights_delay_analysis_2025_01.csv')
print(ops.shape)
print(delay.shape)
print(delay['ARR_DEL15'].value_counts(dropna=False).to_dict())
