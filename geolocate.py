import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
import pickle
import os

# --- Configuration ---
APP_NAME = 'czech_city_geocoder'
GEO_CITY_COL = 'geo_city'
CACHE_FILE = 'geocode_cache.pkl'
INPUT_FILE = './data/referendums/held_referendums.csv'  # Input file with referendums data
OUTPUT_FILE = './data/referendums/held_referendums_with_coords.csv'  # Save progress here

# --- Post-edits
d = pd.read_csv(OUTPUT_FILE)
d.loc[d['lokalita'] == "Miskovice - mč               (Kutná Hora, STČ)", 'geo_city'] = "Miskovice, Kutná Hora, Střední čechy, Česká republika"
d.loc[d['lokalita'] == "Abertamy a přidružená část Hřebečná (Karlovy Vary, KVK)", 'geo_city'] = "Abertamy, Karlovy Vary, Česká republika"
d.loc[d['lokalita'] == "Valaššské Meziříčí        (Vsetín, ZLK)", 'geo_city'] = "Valašské Meziříčí, Vsetín, Zlínský kraj, Česká republika"
d.loc[d['lokalita'] == "Suché Lazce                   (mč Opava, MSK)", 'geo_city'] = "Suché Lazce, Opava, Moravskoslezský kraj, Česká republika"
d.loc[d['lokalita'] == "Dolní Tošenovice (Frýdek - Místek, MSK) ", 'geo_city'] = "Dolní Tošanovice, Frýdek - Místek, Moravskoslezský kraj, Česká republika"
d.loc[d['lokalita'] == "Mníšek pod Brdy (Černošice, STČ)", 'geo_city'] = "Čisovice, Mníšek pod Brdy, Střední Čechy, Česká republika"
d.loc[d['lokalita'] == "Oldříš                        (Polička, PAR)", 'geo_city'] = "Oldříš, Pardubický kraj, Česká republika"
d.loc[d['lokalita'] == "Horní Újezd (Litomyšl, PAR)", 'geo_city'] = "Horní Újezd, Pardubický kraj, Česká republika"
d.loc[d['lokalita'] == "Hnojník                  (Třinec, MSK)", 'geo_city'] = "Hnojník, Moravskoslezský kraj, Česká republika"
d.loc[d['lokalita'] == "Trstěnice                (Litomyšl, PAR)", 'geo_city'] = "Trstěnice, Pardubický kraj, Česká republika"
d.loc[d['lokalita'] == "Neurazy              (Nepomuk, PLK)", 'geo_city'] = "Neurazy, Plzeňský kraj, Česká republika"
d.loc[d['lokalita'] == "Svojetice                  (Říčany, STČ)", 'geo_city'] = "Svojetice, Střední Čechy, Česká republika"
d.loc[d['lokalita'] == "Velenov              (Blansko, OLK)", 'geo_city'] = "Velenov, Jihomoravský kraj, Česká republika"
d.loc[d['lokalita'] == "Městská část Praha 8                     (Praha)", 'geo_city'] = "Praha 8, Hlavní město Praha, Česká republika"
d.loc[d['lokalita'] == "Obec Chotilsko              (Příbram, STK)", 'geo_city'] = "Chotilsko, Střední Čechy, Česká republika"
d.loc[d['lokalita'] == "Škvorec               (Praha - výchd)", 'geo_city'] = "Škvorec, Praha-Východ, Česká republika"
d.loc[d['lokalita'] == "městský obvod Ostrava-Jih       (Ostrava, MSK)", 'geo_city'] = "Ostrava-Jih, Moravskoslezský kraj, Česká republika"
d.loc[d['lokalita'] == "Městská část Praha - Dolní Chabry       (Praha)", 'geo_city'] = "Dolní Chabry, Hlavní město Praha, Česká republika"
d.loc[d['lokalita'] == "městská část Suché Lazce               (Opava, MSK)", 'geo_city'] = "Suché Lazce, Opava, Moravskoslezský kraj, Česká republika"
d.loc[d['lokalita'] == "městský obvod Plzeň 7 - Radčice       (Plzeň, PLK)", 'geo_city'] = "Plzeň 7 - Radčice, Plzeňský kraj, Česká republika"
d.loc[d['lokalita'] == "Jammé          (Jihlava, VYS)", 'geo_city'] = "Jamné, Kraj Vysočina, Česká republika"
d.loc[d['lokalita'] == "MO Ústí nad Labem - Střekov                         (Ústí nad Labem, ÚSK)", 'geo_city'] = "Ústí nad Labem - Střekov, Ústecký kraj, Česká republika"
d.loc[d['lokalita'] == "Lysá nad Labem (Nymburk, ÚSK)", 'geo_city'] = "Lysá nad Labem, Střední Čechy, Česká republika"
d.loc[d['lokalita'] == "Městský obvod Stará Bělá (Ostrava - město, MSK)", 'geo_city'] = "Stará Bělá, Moravskoslezský kraj, Česká republika"
d.loc[d['lokalita'] == "MČ Praha - Řeporyje        (Praha, PHA)", 'geo_city'] = "Řeporyje, Hlavní město Praha, Česká republika"
d.loc[d['lokalita'] == "MČ Praha - Lipence        (Praha, PHA)", 'geo_city'] = "Lipence, Hlavní město Praha, Česká republika"
d.to_csv(OUTPUT_FILE, index=False)

# --- Initialize Geolocator ---
geolocator = Nominatim(user_agent=APP_NAME, timeout=10)

# --- Load or Initialize Cache ---
geocode_cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'rb') as f:
        geocode_cache = pickle.load(f)

# --- Load or Initialize DataFrame ---
if os.path.exists(OUTPUT_FILE):
    df_cleaned = pd.read_csv(OUTPUT_FILE)
    # Ensure coordinate columns exist
    if 'city_latitude' not in df_cleaned.columns:
        df_cleaned['city_latitude'] = pd.NA
    if 'city_longitude' not in df_cleaned.columns:
        df_cleaned['city_longitude'] = pd.NA
else:
    # Load your original dataframe here
    df_cleaned = pd.read_csv(INPUT_FILE)
    # Initialize coordinate columns
    df_cleaned['city_latitude'] = pd.NA
    df_cleaned['city_longitude'] = pd.NA

# --- Geocoding Function with Retry and Caching ---
def geocode_with_retry(city, max_retries=3):
    if city in geocode_cache:
        return geocode_cache[city]

    for _ in range(max_retries):
        try:
            location = geolocator.geocode(city, exactly_one=True, timeout=10)
            if location:
                result = (location.latitude, location.longitude)
                geocode_cache[city] = result
                return result
            else:
                geocode_cache[city] = (pd.NA, pd.NA)
                return (pd.NA, pd.NA)
        except (GeocoderTimedOut, GeocoderUnavailable):
            time.sleep(1)
            continue

    geocode_cache[city] = (pd.NA, pd.NA)
    return (pd.NA, pd.NA)

# --- Apply Geocoding to DataFrame ---
def geocode_dataframe(df):
    for idx, row in df.iterrows():
        city = row[GEO_CITY_COL]
        # Skip if coordinates are already present
        if pd.notna(row.get('city_latitude')) and pd.notna(row.get('city_longitude')):
            continue

        lat, lon = geocode_with_retry(city)
        df.loc[idx, 'city_latitude'] = lat
        df.loc[idx, 'city_longitude'] = lon

    return df

# --- Save Cache and Progress ---
def save_progress(df, cache):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)
    df.to_csv(OUTPUT_FILE, index=False)

# --- Run the Process ---
# Example: Process in chunks to save progress frequently
chunk_size = 50
for i in range(0, len(df_cleaned), chunk_size):
    chunk = df_cleaned.iloc[i:i + chunk_size]
    geocode_dataframe(chunk)
    save_progress(df_cleaned, geocode_cache)
    print(f"Processed up to row {i + chunk_size}")

print("Geocoding complete! Results saved to:", OUTPUT_FILE)

print(x)




# Apply geocoding with retry logic
df_cleaned[['city_latitude', 'city_longitude']] = df_cleaned['geo_city'].apply(
    lambda x: geocode_with_retry(x)
).apply(pd.Series)


# Save the final dataset of held referendums to csv file
d = df_fin.to_csv('./data/referendums/held_referendums.csv', index=False)

# Prepare geo string for district geolocation
# get the polygons here https://github.com/MichalZem/CzechGPSPolygonList/tree/master
#df_cleaned['geo_district'] = df_cleaned['okres_fin'] + ", " + df_cleaned['kraj_fin'] + ", Česká republika"


# Prepare district geolocation
df_cleaned['district_geojson'] = df_cleaned['okres_fin'].apply(
    lambda x: next((f.replace('.geojson', '') for f in os.listdir('data/polygons/districts') if unidecode.unidecode(f.replace('.geojson', '').replace(' ', '').replace('-', '')).lower() == unidecode.unidecode(x.replace(' ', '').replace('-', '')).lower()), None)
)

# Check districts that weren't matched, especially their kraj_fin, okres_fin and district_geojson fields
print(df_cleaned[df_cleaned['district_geojson'].isna() & ~df_cleaned['okres_fin'].isna()][['kraj_fin', 'okres_fin', 'district_geojson']])
