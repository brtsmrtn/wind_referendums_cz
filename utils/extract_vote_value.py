import re
import pandas as pd
from typing import Union
from data.types import VoteExtractionResult, ExtractionType
from pandas._libs.missing import NAType

def extract_vote_value(
    value: Union[str, float, int, NAType],
    extract_type: ExtractionType = "count"
) -> VoteExtractionResult:
    """Extracts either the numeric vote count or percentage from formatted strings.

    Parses strings like '102 (39.53%)' to extract either the integer vote count (e.g., 102)
    or the percentage value (e.g., 39.53). Handles missing values and invalid inputs gracefully.

    Args:
        value (Union[str, float, int, NAType]):
            The input value, which can be a string (e.g., '102 (39.53%)'), a numeric value,
            or a pandas missing value indicator (`pd.NA` or `None`).
        extract_type (ExtractionType, optional):
            Specifies whether to extract the vote count ("count") or the percentage ("percent").
            Defaults to "count".

    Returns:
        VoteExtractionResult:
            - If `extract_type="count"`, returns the vote count as an integer.
            - If `extract_type="percent"`, returns the percentage as a float.
            - Returns `0` or `0.0` if the input is invalid or missing.

    Raises:
        ValueError: If `extract_type` is not "count" or "percent".

    Examples:
        >>> extract_vote_value('102 (39.53%)', extract_type="count")
        102
        >>> extract_vote_value('102 (39.53%)', extract_type="percent")
        39.53
        >>> extract_vote_value(pd.NA, extract_type="count")
        0
        >>> extract_vote_value('invalid_string', extract_type="percent")
        0.0
    """
    if pd.isna(value):
        return 0 if extract_type == "count" else 0.0  # Handle missing values

    # Use regex to extract the vote count and percentage
    match = re.match(r'^\s*(\d+)\s*\(([\d.]+)%\)$', str(value))
    if match:
        vote_count = int(match.group(1))
        percent = float(match.group(2))

        if extract_type == "count":
            return vote_count
        elif extract_type == "percent":
            return percent
        else:
            raise ValueError("Invalid `extract_type`. Use 'count' or 'percent'.")

    # Fallback: try to convert the entire value to a number
    try:
        numeric_value = float(str(value).strip())
        return int(numeric_value) if extract_type == "count" else numeric_value
    except (ValueError, TypeError):
        return 0 if extract_type == "count" else 0.0  # Default if parsing fails