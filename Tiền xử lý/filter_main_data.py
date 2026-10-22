#!/usr/bin/env python3
"""
Filter main_data.parquet using unique_ids from filtered_building.csv
Remove dataset column and columns ending with _1
Save to CSV
"""

import duckdb
import pandas as pd
import os

def filter_main_data():
    """Filter main_data.parquet and save to CSV"""
    
    print("="*70)
    print("FILTERING MAIN DATA")
    print("="*70)
    
    # File paths
    main_data_file = 'main_data.parquet'
    filter_file = 'filtered_building.csv'
    output_file = 'filtered_main_data.csv'
    
    # Check if files exist
    if not os.path.exists(main_data_file):
        print(f"\n❌ Error: {main_data_file} not found")
        return None
    
    if not os.path.exists(filter_file):
        print(f"\n❌ Error: {filter_file} not found")
        return None
    
    # Initialize DuckDB connection
    conn = duckdb.connect()
    
    try:
        # Step 1: Read filtered_building.csv to get list of unique_ids
        print(f"\n📥 Step 1: Reading {filter_file}...")
        filter_df = pd.read_csv(filter_file)
        unique_ids = filter_df['unique_id'].unique().tolist()
        print(f"   ✅ Found {len(unique_ids):,} unique_ids to filter")
        
        # Step 2: Read main_data.parquet and get column info
        print(f"\n📥 Step 2: Reading {main_data_file}...")
        columns_info = conn.execute(f"""
            DESCRIBE SELECT * FROM read_parquet('{main_data_file}')
        """).fetchall()
        
        all_columns = [col[0] for col in columns_info]
        print(f"   ✅ Found {len(all_columns)} columns")
        
        # Step 3: Identify columns to remove
        # Remove 'dataset' column
        # Remove columns ending with '_1'
        columns_to_remove = ['dataset'] + [col for col in all_columns if col.endswith('_1')]
        columns_to_keep = [col for col in all_columns if col not in columns_to_remove]
        
        print(f"\n🗑️  Step 3: Removing columns:")
        print(f"   Columns to remove: {columns_to_remove}")
        print(f"   Columns to keep: {len(columns_to_keep)} columns")
        
        # Step 4: Filter data
        print(f"\n🔄 Step 4: Filtering data...")
        
        # Create a temporary table with filtered unique_ids (more efficient for large lists)
        filter_df_temp = pd.DataFrame({'unique_id': unique_ids})
        conn.register('filter_ids_temp', filter_df_temp)
        conn.execute("CREATE OR REPLACE TEMP TABLE filter_ids AS SELECT * FROM filter_ids_temp")
        
        # Build the SELECT statement with column filtering
        # Use main. prefix for all columns to avoid ambiguity
        columns_str = ', '.join([f"main.\"{col}\"" for col in columns_to_keep])
        
        # Get initial count
        total_count = conn.execute(f"""
            SELECT COUNT(*) FROM read_parquet('{main_data_file}')
        """).fetchone()[0]
        print(f"   Total rows in main_data: {total_count:,}")
        
        # Filter and select columns using JOIN (more efficient)
        filtered_query = f"""
            SELECT {columns_str}
            FROM read_parquet('{main_data_file}') main
            INNER JOIN filter_ids f ON main.unique_id = f.unique_id
        """
        
        filtered_count = conn.execute(f"""
            SELECT COUNT(*) FROM ({filtered_query})
        """).fetchone()[0]
        print(f"   Filtered rows: {filtered_count:,}")
        
        # Step 5: Save to CSV
        print(f"\n💾 Step 5: Saving to {output_file}...")
        conn.execute(f"""
            COPY ({filtered_query}) TO '{output_file}' (FORMAT CSV, HEADER, DELIMITER ',')
        """)
        
        # Verify file was created
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # Size in MB
            print(f"   ✅ Successfully saved {output_file}")
            print(f"   📊 File size: {file_size:.2f} MB")
            print(f"   📊 Rows: {filtered_count:,}")
            print(f"   📊 Columns: {len(columns_to_keep)}")
            
            # Show sample of saved data
            print(f"\n📋 Sample of saved data (first 5 rows):")
            sample = conn.execute(f"""
                SELECT * FROM read_csv('{output_file}') LIMIT 5
            """).fetchdf()
            print(sample.to_string())
            
        else:
            print(f"   ❌ Error: File was not created")
            return None
        
        print(f"\n✅ Process completed successfully!")
        print(f"   Output file: {output_file}")
        
        return {
            'output_file': output_file,
            'row_count': filtered_count,
            'column_count': len(columns_to_keep),
            'removed_columns': columns_to_remove
        }
        
    except Exception as e:
        print(f"\n❌ Error processing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()


if __name__ == '__main__':
    result = filter_main_data()
