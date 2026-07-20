import warnings 
import config
import pandas as pd
import os.path
import sys

def load_data(debug = True):

    # Initialize config (file paths, column names, etc.)
    if(debug): config.init()

    if not os.path.exists(config.REFERENDUMS_TO_LOAD):
        sys.exit("The input file is missing.")

    # Due to bad excel files
    # turn off warnings temporarily
    if not (debug): warnings.simplefilter('ignore')

    # Read in raw .xlsx data as pandas DataFrame
    df = pd.read_excel(config.REFERENDUMS_TO_LOAD, header = 0, skiprows = 1, skipfooter = 11)
    if(debug): print(f"Loaded {len(df)} rows and {len(df.columns)} columns from {config.REFERENDUMS_TO_LOAD}")

    # Turn warnings on again
    if not (debug): warnings.simplefilter("default")

    # Name columns
    df.columns = config.COLUMN_NAMES
    
    # Save the loaded df as csv file
    df_loaded = df.to_csv(config.REFERENDUMS_LOADED, index=False)
    
    return(df_loaded)

if __name__ == '__main__':
    load_data(True)