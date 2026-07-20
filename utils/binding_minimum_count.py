import re
import pandas as pd
from typing import Union, Optional
from data.types import BindingMinimumCount
from pandas._libs.missing import NAType

def binding_minimum_count(
    value: Union[str, NAType]
) -> BindingMinimumCount:
    """Extracts the numerical value from strings like "ANO      (525)" as the binding minimum count.

    This function is designed to parse strings where a numerical value is enclosed in parentheses,
    such as "ANO      (525)", and extract the number (e.g., 525) as the minimum count.
    It handles missing values and invalid inputs gracefully.

    Args:
        value (Union[str, NAType]):
            The input value, which can be a string (e.g., "ANO      (525)") or a pandas
            missing value indicator (`pd.NA` or `None`).

    Returns:
        int:
            The extracted numerical value (e.g., 525). Returns `0` if:
            - The input is a missing value (`pd.NA` or `None`).
            - The input does not match the expected format.
            - The numerical extraction fails.

    Examples:
        >>> extract_minimum_count("ANO      (525)")
        525
        >>> extract_minimum_count("NE      (300)")
        300
        >>> extract_minimum_count(pd.NA)
        0
        >>> extract_minimum_count("invalid_string")
        0
    """
    if pd.isna(value):
        return 0  # Handle missing values

    # Use regex to extract the numerical value inside parentheses
    match = re.search(r'\(\s*(\d+)\s*\)', str(value))
    if match:
        return int(match.group(1))
    else:
        return 0  # Default if extraction fails