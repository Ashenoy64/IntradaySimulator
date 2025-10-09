import pandas as pd
from Operations import OperationBase
from typing import Literal, Optional
import glob
from Settings import FORMAT_DATA_PATH, DATA_STORE_PATH
import os

def _format_data( df:pd.DataFrame, operations:list[OperationBase] )->pd.DataFrame:
    for operation in operations:
        if operation.isInplace():
            df = operation.operate(df)
        else:
            columns = operation.getOperationColumns()
            operatedColumn = operation.operate( df[columns] )
            try:
                df[columns] = operatedColumn

            except ValueError as ve:
                print("Assignment failed: ", ve)
                
                # Attempt a best-effort fallback: align on index
                try:
                    if not operatedColumn.index.equals(df.index):
                        # Align by reindexing, fill missing values as needed (e.g., with NaN)
                        df[columns] = operatedColumn.reindex(df.index)
                    else:
                        raise
                except Exception as e:
                    print("Fallback copy also failed: ", e)

            except Exception as e:
                print("Unexpected error during assignment: ", e)
                    
    return df


def sanity_test(
    csvs: list[str],
    column_merge_mode: Literal['ignore', 'merge', 'default'],
    columns: Optional[list[str]] = None
) -> list[str]:
    if columns is None:
        columns = []
    required_columns = set(columns)
    all_columns = set()
    first_file = True
    for file_path in csvs:
        df_columns = set(pd.read_csv(file_path, nrows=0).columns)
        if required_columns:
            if not required_columns.issubset(df_columns):
                missing = required_columns - df_columns
                raise Exception(f"FILE: {file_path} missing required columns: {missing}")
            continue

        if first_file:
            all_columns = df_columns
            first_file = False
            continue

        common_columns = df_columns & all_columns
        extra_cols_in_file = df_columns - common_columns
        extra_cols_in_all_file = all_columns - common_columns

        if extra_cols_in_all_file:
            if column_merge_mode == 'default':
                raise Exception(f"FILE: {file_path} has fewer columns than already seen files: {extra_cols_in_all_file}")
        if extra_cols_in_file:
            if column_merge_mode == 'default':
                raise Exception(f"FILE: {file_path} has more columns than already seen files: {extra_cols_in_file}")

        if column_merge_mode == 'ignore':
            all_columns = common_columns
        elif column_merge_mode == 'merge':
            all_columns = all_columns | df_columns

    return list(required_columns) if required_columns else list(all_columns)

def format_data(
    data_dir: str,
    operations: list[OperationBase],
    column_merge_mode: Literal['ignore', 'merge', 'default'] = 'default',
    columns: Optional[list[str]] = None,
    write_csv: bool = False,
    return_empty: bool = False,
    name: str = 'strange'
) -> pd.DataFrame | None:
    if columns is None:
        columns = []
    directory_path = os.path.join(DATA_STORE_PATH, data_dir)
    all_files = glob.glob(os.path.join(directory_path, "*.csv"))
    columns = sanity_test(all_files, column_merge_mode, columns)

    df_list = []
    for file_path in all_files:
        df = pd.read_csv(file_path)[columns]
        formatted_df = _format_data(df, operations)
        df_list.append(formatted_df)

    combined_df = pd.concat(df_list, ignore_index=True)

    if write_csv:
        out_path = os.path.join(FORMAT_DATA_PATH, f"{name}.csv")
        combined_df.to_csv(out_path, index=False)

    if return_empty:
        return None
    return combined_df
