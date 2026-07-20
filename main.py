import config
from load import load_data
from clean import clean_data

config.init()

df_loaded = load_data(False)

df_cleaned = clean_data(False, df_loaded)

print(df_cleaned)