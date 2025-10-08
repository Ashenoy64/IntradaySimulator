import pandas as pd
from Operations import OperationBase
from typing import Literal


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



def format_data(
        data_dir: str,
        operations: list[OperationBase],
        column_merge_mode:Literal['ignore', 'merge' , 'default'] ='default' ,
        save_scaler:bool = False,
        unified_scaler:bool = False,
        write_csv:bool = False,
        return_empty:bool = False,
        name: str = 'strange'
)->pd.DataFrame | None:
    pass