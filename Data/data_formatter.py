import pandas as pd
from .Operations import OperationBase
from typing import Literal, Optional
import glob
from Settings import FORMAT_DATA_PATH, DATA_STORE_PATH
import os
from .RegexStr import RegexString

def expand_regex( columns:list[str], operation_columns:list[str] )->list[str]:
    ops_cols = set()
    for col in operation_columns:
        if not isinstance( col, RegexString ):
            ops_cols.add( col )
        else:
            for _col in columns:
                if col == _col:
                    ops_cols.add( _col )
    return list( ops_cols )

def format_data( df:pd.DataFrame, operations:list[OperationBase], fileName:Optional[str]=None )->pd.DataFrame:
    df_columns = set( df.columns )
    for operation in operations:
        operation_columns = operation.getOperationColumns()
        
        if any( isinstance( item, RegexString ) for item in operation_columns ):
            operation_columns = expand_regex( list( df.columns ), operation_columns )
        
        operation_columns = [ col for col in df_columns if col in operation_columns ]

        if not operation_columns:
            if fileName:
                print( f"Skipping.. { str( operation.__class__.__name__ ) } for { fileName }" )
            else:
                print( f" Skipping.. { str( operation.__class__.__name__ ) }" )
            continue

        if operation.isInplace():
            df = operation.operate( df )
        else:
            operatedColumn = operation.operate( df[ operation_columns ] )
            try:
                df[ operatedColumn.columns ] = operatedColumn

            except ValueError as ve:
                print( "Assignment failed: ", ve )
                
                # Attempt a best-effort fallback: align on index
                try:
                    if not operatedColumn.index.equals( df.index ):
                        # Align by reindexing, fill missing values as needed (e.g., with NaN)
                        df[ operation_columns ] = operatedColumn.reindex( df.index )
                    else:
                        raise
                except Exception as e:
                    print( "Fallback copy also failed: ", e )

            except Exception as e:
                print( "Unexpected error during assignment: ", e )
        df_columns = set( df.columns )        
    return df

def sanity_test(
    csvs:list[str],
    column_merge_mode:Literal[ 'ignore', 'merge', 'default' ],
    columns:Optional[list[str]] = None
) -> list[str]:
    if columns is None:
        columns = []
    required_columns = set( columns )
    all_columns = set()
    first_file = True
    for file_path in csvs:
        df_columns = set( pd.read_csv( file_path, nrows = 0 ).columns )
        if required_columns:
            if not required_columns.issubset( df_columns ):
                missing = required_columns - df_columns
                raise Exception( f"FILE: { file_path } missing required columns: { missing }" )
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
                raise Exception( f"FILE: { file_path } has fewer columns than already seen files: { extra_cols_in_all_file }" )
        if extra_cols_in_file:
            if column_merge_mode == 'default':
                raise Exception( f"FILE: { file_path } has more columns than already seen files: { extra_cols_in_file }" )

        if column_merge_mode == 'ignore':
            all_columns = common_columns
        elif column_merge_mode == 'merge':
            all_columns = all_columns | df_columns

    return list( required_columns ) if required_columns else list( all_columns )

def collect_and_format_data(
    data_dir:str,
    operations:list[OperationBase],
    column_merge_mode:Literal['ignore', 'merge', 'default'] = 'default',
    columns:Optional[list[str]] = None,
    write_csv:bool = False,
    name:str|None = None,
) -> Optional[pd.DataFrame]:

    if write_csv and not name:
        raise Exception("name for file is not provided")

    if columns is None:
        columns = []
    directory_path = os.path.join( DATA_STORE_PATH, data_dir )
    all_files = glob.glob( os.path.join( directory_path, "*.csv" ) )
    columns = sanity_test( all_files, column_merge_mode, columns )

    df_list = []
    for file_path in all_files:
        df = pd.read_csv( file_path )
        cols = [ col for col in df.columns if col in columns ]
        df = df[ cols ]
        formatted_df = format_data( df, operations, os.path.basename( file_path ) )
        df_list.append( formatted_df )

    combined_df = pd.concat( df_list, ignore_index = True )

    if write_csv:
        out_path = os.path.join( FORMAT_DATA_PATH, f"{ name }.csv" )
        combined_df.to_csv( out_path, index = False )

    return combined_df
