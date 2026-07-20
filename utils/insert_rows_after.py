import pandas as pd
from typing import Dict, List

def insert_rows_after(
    df: pd.DataFrame,
    updates: Dict[str, Dict[str, Dict[str, str]]],
    key_col: str = 'poradi'
) -> pd.DataFrame:
    """
    Inserts new rows after specified rows (by key_col) and updates the original row.
    Allows manual specification of new rows and their contents.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        updates (Dict[str, Dict[str, Dict[str, str]]]):
            A dictionary where:
            - Key: key_col of the row to update/insert after.
            - Value: Dictionary with:
                - Key 'update': Dictionary of column:value to update the original row.
                - Key 'insert': List of dictionaries, each representing a new row to insert.

    Returns:
        pd.DataFrame: The modified DataFrame.
    """
    df = df.copy()
    for nr, actions in updates.items():
        # Find the index of the row with the specified key_col
        idx = df.index[df[key_col] == nr].tolist()
        if not idx:
            raise ValueError(f"No row found with poradi={nr}")
        idx = idx[0]

        # Update the original row if specified
        if 'update' in actions:
            for col, val in actions['update'].items():
                df.at[idx, col] = val

        # Insert new rows if specified
        if 'insert' in actions:
            new_rows = actions['insert']
            df_new_rows = pd.DataFrame(new_rows)
            # Insert after the original row
            df = pd.concat([
                df.iloc[:idx + 1],
                df_new_rows,
                df.iloc[idx + 1:]
            ], ignore_index=True)

    return df