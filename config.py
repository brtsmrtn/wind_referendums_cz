import pandas as pd
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_colwidth', 1000)  # Don't truncate column content
pd.set_option('display.width', None)        # Don't wrap lines
pd.set_option("display.max_rows", None)    # Show all rows
pd.set_option("display.expand_frame_repr", True)    # Expand to fit content


from utils.extract_date_from_filename import extract_date_from_filename

RECENT_SHEET = 'Mistni_referenda-tabulka_hlaseni_-_20250121.xlsx'

def init():
    global REFERENDUMS_FOLDER
    REFERENDUMS_FOLDER = './data/referendums'

    global REFERENDUMS_TO_LOAD
    REFERENDUMS_TO_LOAD = f'{REFERENDUMS_FOLDER}/src/{RECENT_SHEET}'

    global REFERENDUMS_SHEET_DATE
    REFERENDUMS_SHEET_DATE = extract_date_from_filename(REFERENDUMS_TO_LOAD)

    global REFERENDUMS_LOADED
    REFERENDUMS_LOADED = f'{REFERENDUMS_FOLDER}/{REFERENDUMS_SHEET_DATE}_loaded.csv'

    global REFERENDUMS_CLEANED
    REFERENDUMS_CLEANED = f'{REFERENDUMS_FOLDER}/{REFERENDUMS_SHEET_DATE}_cleaned.csv'

    global COLUMN_NAMES
    COLUMN_NAMES = ['poradi',   
                    'lokalita',
                    'otazka',
                    'datum',
                    'opravnene_osoby',
                    'ucast',
                    'platnost_referenda',
                    'pro',
                    'proti',
                    'zavaznost',
                    'platnost_hlasovani']