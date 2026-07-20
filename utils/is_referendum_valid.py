import pandas as pd
from typing import Union
from data.types import ReferendumValidityStatus
from pandas._libs.missing import NAType

def is_referendum_valid(
    value: Union[str, NAType]
) -> ReferendumValidityStatus:
    """Determines whether a referendum is valid based on the "platnost_referenda" column.

    In the Czech Republic, the validity of a local referendum is determined by whether it meets
    the legal requirements for participation and procedure. This function checks the "platnost_referenda"
    column, which indicates whether the referendum is considered valid ("ANO") or invalid ("NE").

    Args:
        value (Union[str, NAType]):
            The input value, which can be a string (e.g., "ANO" or "NE") or a pandas
            missing value indicator (`pd.NA` or `None`).

    Returns:
        bool:
            - `True` if the referendum is valid ("ANO").
            - `False` if the referendum is invalid ("NE") or if the input is missing or invalid.

    Examples:
        >>> is_referendum_valid("ANO")
        True
        >>> is_referendum_valid("NE")
        False
        >>> is_referendum_valid(pd.NA)
        False
        >>> is_referendum_valid("invalid_string")
        False
    """
    if pd.isna(value):
        return False  # Handle missing values

    # Check if the value is "ANO" (case-insensitive)
    return str(value).upper() == "ANO"