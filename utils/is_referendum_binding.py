import re
import pandas as pd
from typing import Union
from data.types import ReferendumBindingStatus
from pandas._libs.missing import NAType

def is_referendum_binding(
    value: Union[str, NAType]
) -> ReferendumBindingStatus:
    """Determines whether a referendum result is binding based on the vote outcome.

    According to Czech law (since July 1, 2008), a local referendum is binding if:
    1. A majority of the participants (over 50%) voted in favor ("ANO").
    2. At least 25% of the eligible voters (registered in the voter list) participated in the referendum.

    This function focuses on the first condition: whether the majority of participants voted "ANO".
    It parses strings like "ANO (675)" or "NE (675)" and returns `True` if the result is "ANO" (binding)
    and `False` if the result is "NE" (non-binding).

    Args:
        value (Union[str, NAType]):
            The input value, which can be a string (e.g., "ANO (675)" or "NE (675)") or a pandas
            missing value indicator (`pd.NA` or `None`).

    Returns:
        bool:
            - `True` if the referendum result is "ANO" (binding).
            - `False` if the referendum result is "NE" (non-binding) or if the input is invalid/missing.

    Examples:
        >>> is_referendum_binding("ANO (675)")
        True
        >>> is_referendum_binding("NE (675)")
        False
        >>> is_referendum_binding(pd.NA)
        False
        >>> is_referendum_binding("invalid_string")
        False
    """
    if pd.isna(value):
        return False  # Handle missing values

    # Use regex to extract the decision (ANO or NE)
    match = re.match(r'^\s*(ANO|NE)\s*\(\d+\)$', str(value).upper())
    if match:
        decision = match.group(1)
        return decision == "ANO"
    else:
        return False  # Default for invalid inputs