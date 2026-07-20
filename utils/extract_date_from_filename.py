import re
from typing import Optional
import sys
import os.path


def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    Extracts a date from a filename and returns it in YYYY-MM-DD format.

    Args:
        filename (str): The filename containing a date in YYYYMMDD format.

    Returns:
        Optional[str]: The extracted date as a string in YYYY-MM-DD format.
                      Returns None if no date is found.

    Example:
        >>> extract_date_from_filename(
        ...     './data/referendums/Mistni_referenda-tabulka_hlaseni_-_20251002.xlsx'
        ... )
        '2025-10-02'
    """
    if not os.path.exists(filename):
        sys.exit("The input file is missing.")

    match = re.search(r'(\d{8})\.xlsx$', filename)
    if not match:
        return None

    date_str = match.group(1)
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"