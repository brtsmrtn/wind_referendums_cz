import re
import numpy as np
from datetime import datetime

def extract_year_from_value(text):
    """
    Extracts the first date from a string or datetime object in various formats and returns it as YYYY-MM-DD.
    Handles formats like:
    - 2006-06-24 00:00:00 -> 2006-06-24
    - 20. -21.10.2006 -> 2006-10-20
    - 20.-21.9.2024 -> 2024-09-20
    - 2. - 3. 10. 2020 -> 2020-10-02
    - 16. 6. 2018   9:00 - 18:00 -> 2018-06-16
    - 7. 10. a 8. 10. 2016 -> 2016-10-07
    - datetime(2006, 3, 25, 0, 0) -> 2006-03-25
    Prints a warning if no match is found. Handles NaN/None values.
    """
    if text is None or (isinstance(text, float) and np.isnan(text)):
        # print(f"Warning: a year in line containing 'NaN' hasn't been recognized")
        return None
    
    # If input is a datetime object, convert to string
    if isinstance(text, datetime):
        text = text.strftime("%Y-%m-%d %H:%M:%S")

    # Normalize whitespace
    text = ' '.join(text.split())

    # Regex to match the first date
    match = re.search(
        r'(?:(\d{4})-(\d{2})-(\d{2}))|(?:(\d{1,2})\s*[.-]?\s*(\d{1,2})\s*[.-]?\s*(\d{4}))',
        text
    )
    if match:
        if match.group(1):  # YYYY-MM-DD
            return match.group(1)
        else:  # DD.MM.YYYY or DD-MM-YYYY
            year = match.group(6)
            return year
    else:
        print(f"Warning: a year in line containing '{text}' hasn't been recognized")
        return None

# Example usage:
""" examples = [
    "2006-06-24 00:00:00",
    "20. -21.10.2006",
    np.nan,
    "20.-21.9.2024",
    "2. - 3. 10. 2020",
    None,
    "16. 6. 2018   9:00 - 18:00",
    "7. 10. a 8. 10. 2016",
    datetime(2006, 3, 25, 0, 0),
    "This is not a date",
]

for example in examples:
    print(f"{example} -> {extract_year_from_value(example)}") """