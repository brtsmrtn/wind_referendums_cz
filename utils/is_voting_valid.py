import pandas as pd
from typing import Union
from data.types import VotingValidityStatus
from pandas._libs.missing import NAType

def is_voting_valid(
    value: Union[str, NAType]
) -> VotingValidityStatus:
    """Determines whether the voting in a referendum is valid based on the "platnost_hlasovani" column.

    The "platnost_hlasovani" column indicates whether the voting process itself is valid.
    If the value is "hlasování neplatné", the voting is considered invalid. Otherwise, it is valid.

    Args:
        value (Union[str, NAType]):
            The input value, which can be a string (e.g., "hlasování neplatné" or any other value)
            or a pandas missing value indicator (`pd.NA` or `None`).

    Returns:
        bool:
            - `True` if the voting is valid (i.e., the value is not "hlasování neplatné").
            - `False` if the voting is invalid (i.e., the value is "hlasování neplatné") or if the input is missing.

    Examples:
        >>> is_voting_valid("hlasování neplatné")
        False
        >>> is_voting_valid(pd.NA)
        True
        >>> is_voting_valid("")
        True
    """
    if pd.isna(value):
        return True  # Handle missing values

    # Check if the value is "hlasování neplatné"
    return str(value).strip().lower() != "hlasování neplatné"