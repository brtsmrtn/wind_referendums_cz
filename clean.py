from ctypes import cast
import sys
import os.path
import unidecode
from utils.insert_rows_after import insert_rows_after
from utils.extract_year_from_value import extract_year_from_value
import numpy as np
import re
import pandas as pd
import data.types
import config
from utils import is_referendum_valid, is_referendum_binding, is_voting_valid, binding_minimum_count


# Utility function to forward-fill only specific columns based on a condition
def selective_ffill(df, cols, condition_cols):
    mask = df[condition_cols].isna().all(axis=1)
    df.loc[mask, cols] = df[cols].ffill()
    return df

def clean_data(debug = True, df = None):
    # Initialize config (file paths, column names, etc.)
    if(debug): config.init()

    if not os.path.exists(config.REFERENDUMS_LOADED):
        sys.exit("The loaded file is missing.")

    if df is None:
        df = pd.read_csv(config.REFERENDUMS_LOADED)

    # fix types
    df['poradi'] = df['poradi'].astype("Int32")

    # --- clean up: separate referendum instances properly ---
    
    # Define columns affected by merged cells
    # Apply forward-fill only when BOTH 'poradi' and 'lokalita' are NaN
    columns_to_check = ['poradi', 'lokalita']
    columns_to_fill = ['poradi', 'lokalita', 'datum', 'opravnene_osoby', 'ucast', 'platnost_referenda', 'zavaznost', 'platnost_hlasovani']

    # Neccessary edits before ffill
    df.loc[(df.index == 327) & (df['poradi'].isna()) & (df['lokalita'] == "Lešná (Vsetín, ZLK)"), 'poradi'] = 286
    df.loc[(df.index == 328) & (df['poradi'] == 286) & (df['lokalita'].isna()), 'poradi'] = None
    df.loc[(df.index == 216) & (df['datum'] == "12. 12.                14:00 - 22:00"), 'datum'] = "12. 12. 2014"

    # head first five rows (withoug otazka and opravnene_osoby columns)
    print(df.head()[['poradi', 'lokalita', 'datum', 'opravnene_osoby']])
    updates = {
        3: {
            'update': {
                'poradi': 3,
                'lokalita': 'Opatovice nad Labem (Pardubice, PAK)',
                'otazka': '1. Souhlasíte se vstupem obce do společnosti na energetické využívání odpadů EVO, a.s.?',
                'datum': '2006-06-24 00:00:00',
                'opravnene_osoby': 1352,
                'ucast': 0.547,
                'platnost_referenda': 'ANO',
                'pro': '98 (13,3 %)',
                'proti': '610 (82,5 %)',
                'zavaznost': 'ANO (370)',
                'platnost_hlasovani': np.nan
            },
            'insert': [
                {
                    'poradi': 3,
                    'lokalita': 'Opatovice nad Labem (Pardubice, PAK)',
                    'otazka': '2. Jste pro to, aby obec Opatovice nad Labem souhlasila s umístěním stavby spalovny odpadů nebo zařízení na energetické využívání odpadů na katastrálním území obce Opatovice nad Labem?',
                    'datum': '2006-06-24 00:00:00',
                    'opravnene_osoby': 1352,
                    'ucast': 0.547,
                    'platnost_referenda': 'ANO',
                    'pro': '46 (56,2 %)',
                    'proti': '669 (90,5 %)',
                    'zavaznost': 'ANO (370)',
                    'platnost_hlasovani': np.nan
                }
            ]
        }
    }
    df = insert_rows_after(df, updates, key_col='poradi')
    # show all columns
    print(df.columns)
    # 'poradi', 'lokalita', 'otazka', 'datum', 'opravnene_osoby', 'ucast',
    #   'platnost_referenda', 'pro', 'proti', 'zavaznost',
    #   'platnost_hlasovani'
    # Forward fill only for selected columns and only where the condition is True
    df = selective_ffill(df, cols=columns_to_fill, condition_cols=columns_to_check)

    print(df.loc[2:4][['poradi', 'lokalita', 'datum', 'otazka']])
    print(x)

    # copy data to df_cleaned
    df_cleaned = df.copy()

    # --- clean up: data integrity ---
    # ----- `platnost_fin` `platnost_T` ~ referendum validity ---

    # ->>>
    if(debug): print(df['platnost_referenda'].unique())


    # Define columns of interest
    cols = ['platnost_referenda', 'zavaznost', 'platnost_hlasovani']

    # Standardize 'zavaznost' by removing content in parentheses
    df['zavaznost_clean'] = df['zavaznost'].apply(
        lambda x: re.sub(r'\s*\(.*\)', '', str(x)).strip() if pd.notna(x) else np.nan
    )

    # Use the cleaned column for grouping
    cols_clean = ['platnost_referenda', 'zavaznost_clean', 'platnost_hlasovani']

    # Fill NaN values with a placeholder to distinguish them in grouping
    df_filled = df.copy()
    for col in cols_clean:
        df_filled[col] = df_filled[col].fillna("MISSING")

    # Group by the cleaned columns and count occurrences
    grouped = df_filled.groupby(cols_clean).size().reset_index(name='count')

    # Print overview of counts
    print("Overview of unique combinations and their counts:")
    print(grouped.to_string(index=False))
    print("\n")

    # For each combination, print an example record (excluding 'otazka' and 'lokalita')
    example_cols = [col for col in df.columns if col not in ['otazka', 'lokalita', 'zavaznost_clean']]
    for _, row in grouped.iterrows():
        combination = row[cols_clean].to_dict()
        # Replace "MISSING" with np.nan for filtering
        filter_combination = {k: (np.nan if v == "MISSING" else v) for k, v in combination.items()}

        # Filter the original DataFrame using the cleaned column
        mask = (
            (df['platnost_referenda'] == filter_combination['platnost_referenda']) &
            (df['zavaznost_clean'] == filter_combination['zavaznost_clean']) &
            (df['platnost_hlasovani'] == filter_combination['platnost_hlasovani'])
        )
        examples = df[mask]

        if not examples.empty:
            example = examples.iloc[0][example_cols]
            print(f"Example for combination {combination}:")
            print(example.to_string())
        else:
            print(f"No example found for combination {combination}.")
        print("\n")

    print(x)
    # 'ANO' 'NE' nan '1. ANO       2. ANO']
    # <<<-

    # state of `referendum validity` is non-standard and requires custom solving
    # i.e. `platnost_hlasovani` contains "hlasování neplatné" while platnost_referenda contains "ANO"
    # i.e. 2 there is more possible ways of `platnost_referenda` being "ANO"

    # Normalize the column for comparison
    df_cleaned_platnost_referenda_normalized = df_cleaned['platnost_referenda'].str.lower().str.strip()

    # Assign 'ANO' where 'ano' is found
    df_cleaned['platnost_fin'] = np.where(df_cleaned_platnost_referenda_normalized.str.contains("ano", na=False), 'ANO', df_cleaned['platnost_referenda'])

    # Assign 'NE' where 'ne' is found
    df_cleaned['platnost_fin'] = np.where(df_cleaned_platnost_referenda_normalized.str.contains("ne", na=False), 'NE', df_cleaned['platnost_referenda'])

    # Fix custom cases
    df_cleaned['platnost_fin'] = np.where(df_cleaned['platnost_hlasovani'].str.contains("hlasování neplatné", na=False), 'NE', df_cleaned['platnost_fin'])

    # Check validity
    df_cleaned['platnost_T'] = df_cleaned['platnost_fin'].str.contains('ANO|NE', regex=True, na=False)

    # Determine if the referendum is valid
    df_cleaned['referendum_validity']: pd.Series([data.types.ReferendumValidityStatus]) = df_cleaned['platnost_referenda'].apply(is_referendum_valid.is_referendum_valid) # type: ignore

    # Determine if the referendum is binding
    df_cleaned['referendum_binding']: pd.Series([data.types.ReferendumBindingStatus] )= df_cleaned['zavaznost'].apply(is_referendum_binding.is_referendum_binding) # type: ignore

    # Determine if the voting is valid
    df_cleaned['voting_valid']: pd.Series([data.types.VotingValidityStatus]) = df_cleaned['platnost_hlasovani'].apply(is_voting_valid.is_voting_valid) # type: ignore

    # Extract the binding minimum count
    df_cleaned['binding_minimum_count']: pd.Series([data.types.BindingMinimumCount]) = df_cleaned['zavaznost'].apply(binding_minimum_count.binding_minimum_count) # type: ignore

    # ----- `rok_fin` `rok_T` ~ referendum year ---

    # When it comes to dates, we need just a year of the referendum
    df_cleaned["rok_fin"] = df_cleaned["datum"].map(utils.extract_year_from_value)
    df_cleaned['rok_fin'] = df_cleaned['rok_fin'].astype("Int32")

    # Check validity
    df_cleaned['rok_T'] = ~df_cleaned['rok_fin'].isna()

    # Q: Explore 22 invalid cases:
    # print(df_cleaned[df_cleaned['platnost_T'] == False])
    # - out of which 16 have a normal date set (incl. 12 "neoznámeno", 4 others)
    # print(df_cleaned[(df_cleaned['platnost_T'] == False) & (df_cleaned['rok_T'] == True)])
    # - out of which 6 have no date at all
    # print(df_cleaned[(df_cleaned['platnost_T'] == False) & (df_cleaned['rok_T'] == False)])

    # ----- `obec_fin` `okres_fin` `kraj_fin` `lok_T` ~ geographic location ---

    # Fix custom cases
    # Fix record where obec_okrej_kraj_ consists of "Trokavec, (p.Mirošov, Rokycany, PLK)" to "Trokavec (Rokycany, PLK)"
    df_cleaned.loc[df_cleaned['lokalita'] == 'Trokavec, (p.Mirošov, Rokycany, PLK)', 'lokalita'] = "Trokavec (Rokycany, PLK)"

    # Fix record where obec_okres_kraj consists of "Městský obvod Stará Bělá                          (SM Ostrava, Ostrava - město, MSK)" to "Městský obvod Stará Bělá (Ostrava - město, MSK)"
    df_cleaned.loc[df_cleaned['lokalita'] == 'Městský obvod Stará Bělá                          (SM Ostrava, Ostrava - město, MSK)', 'lokalita'] = "Městský obvod Stará Bělá (Ostrava - město, MSK)"

    # Separate location to city and regional columns to check validity
    df_cleaned['obec_fin'] = pd.Series(df_cleaned['lokalita']).str.split("(").str[0].str.strip()
    df_cleaned['okres_fin'] = pd.Series(df_cleaned['lokalita']).str.split("(").str[1].str.split(",").str[0].str.strip()
    df_cleaned['kraj_fin'] = pd.Series(df_cleaned['lokalita']).str.split("(").str[1].str.split(",").str[1].str.replace(")", "").str.strip()

    # Fix custom cases
    df_cleaned.loc[df_cleaned['kraj_fin'].isna() & (df_cleaned['okres_fin'] == 'Praha)'), 'okres_fin'] = "Praha"
    df_cleaned.loc[df_cleaned['kraj_fin'].isna() & (df_cleaned['okres_fin'].str.contains('Praha', regex=True, na=False)), 'kraj_fin'] = "PHA"
    df_cleaned.loc[df_cleaned['kraj_fin'].isna() & (df_cleaned['okres_fin'] == 'Praha - výchd)'), 'okres_fin'] = "Praha - Východ"

    # Expand regions titles
    # Make a dictionary mapping abbreviations to full names where one or more keys can map to the same value
    region_mapping = {
        "PHA": "Hlavní město Praha",
        "SČ": "Střední čechy",
        "STČ": "Střední čechy",
        "STK": "Střední čechy",
        "JHC": "Jihočeský kraj",
        "JHČ": "Jihočeský kraj",
        "PLK": "Plzeňský kraj",
        "PK": "Pardubický kraj",
        "ULK": "Ústecký kraj",
        "ÚLK": "Ústecký kraj",
        "ÚSK": "Ústecký kraj",
        "LBK": "Liberecký kraj",
        "HKK": "Královéhradecký kraj",
        "KVK": "Karlovarský kraj",
        "KHK": "Královéhradecký kraj",
        "PAK": "Pardubický kraj",
        "PAR": "Pardubický kraj",
        "VYS": "Kraj Vysočina",
        "JHM": "Jihomoravský kraj",
        "JMK": "Jihomoravský kraj",
        "OLK": "Olomoucký kraj",
        "ZLK": "Zlínský kraj",
        "MSK": "Moravskoslezský kraj",
        "SDK": "Střední čechy",
        "JHK": "Jihočeský kraj",
    }

    # Remap the 'kraj_fin' column using the mapping dictionary
    df_cleaned['kraj_fin'] = df_cleaned['kraj_fin'].map(region_mapping)

    # Prepare geo string for city geolocation
    df_cleaned['geo_city'] = df_cleaned['obec_fin'] + ", " + df_cleaned['okres_fin'] + ", " + df_cleaned['kraj_fin'] + ", Česká republika"

    # Print missing mappings
    #print(df_cleaned[df_cleaned['kraj_fin'].isna()])

    # Check validity
    df_cleaned['lok_T'] = ~(df_cleaned['obec_fin'].isna() | df_cleaned['okres_fin'].isna() | df_cleaned['kraj_fin'].isna())


    # --- clean up: final subset ---
    # Keep only rows with valid `platnost_T`, `rok_T`, `lok_T`
    df_fin = df_cleaned[(df_cleaned['platnost_T'] == True) & (df_cleaned['rok_T'] == True) & (df_cleaned['lok_T'] == True)]

    # Check how many rows were dropped
    print(str(df_fin.shape[0]) + " rows after cleaning (pre " + str(df.shape[0]) + ")")

    # Check rows with invalid data
    print(df_cleaned[(df_cleaned['platnost_T'] == False) | (df_cleaned['rok_T'] == False) | (df_cleaned['lok_T'] == False)])



    if(debug): print(f"Cleaned {len(df)} rows and {len(df.columns)} columns from {config.REFERENDUMS_LOADED}")
    
    # Save the cleaned df as csv file
    df_cleaned = df_fin.to_csv(config.REFERENDUMS_CLEANED, index=False)
    
    return(df_cleaned)


if __name__ == '__main__':
    clean_data(True)