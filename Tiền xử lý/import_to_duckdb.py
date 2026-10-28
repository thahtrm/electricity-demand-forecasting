#!/usr/bin/env python3
"""
Import parquet files (weather.parquet, demand.parquet, metadata.parquet) into DuckDB
"""

import duckdb
import os
import pandas as pd
from pandas.tseries.offsets import DateOffset

def import_parquet_to_duckdb():
    """Import parquet files into DuckDB database"""
    
    # Initialize DuckDB connection
    # Use in-memory database or specify a file path for persistent storage
    conn = duckdb.connect('data.duckdb')  # Creates a persistent database file
    # Alternative: conn = duckdb.connect()  # For in-memory database
    
    print("="*70)
    print("Importing Parquet Files to DuckDB")
    print("="*70)
    
    # List of parquet files to import
    parquet_files = {
        'weather': 'weather.parquet',
        'demand': 'demand.parquet',
        'metadata': 'metadata.parquet'
    }
    
    # Check if files exist
    missing_files = []
    for table_name, file_path in parquet_files.items():
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n Error: The following files are missing:")
        for file in missing_files:
            print(f"   - {file}")
        return None
    
    # Import each parquet file
    for table_name, file_path in parquet_files.items():
        print(f"\n📥 Importing {file_path} as table '{table_name}'...")
        
        try:
            # Read parquet file and create table
            # DuckDB can directly read parquet files
            conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_parquet('{file_path}')
            """)
            
            # Get row count
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            # Get column info
            columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
            
            print(f"    Successfully imported {row_count:,} rows")
            print(f"    Columns: {len(columns)}")
            print(f"    Column names: {', '.join([col[0] for col in columns])}")
            
        except Exception as e:
            print(f"    Error importing {file_path}: {str(e)}")
            continue
    
    # Show summary
    print(f"\n{'='*70}")
    print("IMPORT SUMMARY")
    print(f"{'='*70}")
    
    # List all tables
    tables = conn.execute("SHOW TABLES").fetchall()
    print(f"\n📚 Tables in database: {len(tables)}")
    for table in tables:
        table_name = table[0]
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"   - {table_name}: {row_count:,} rows")
    
    # Show sample data from each table
    print(f"\n{'='*70}")
    print("SAMPLE DATA")
    print(f"{'='*70}")
    
    for table_name in parquet_files.keys():
        try:
            sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchdf()
            print(f"\n Sample from '{table_name}' table:")
            print(sample.to_string())
            print()
        except Exception as e:
            print(f"   Warning: Could not fetch sample from {table_name}: {str(e)}")
    
    print(f"\n Import completed!")
    print(f" Database saved to: data.duckdb")
    
    # Check if main_data.parquet exists, if not create it by joining tables
    main_data_file = 'main_data.parquet'
    if not os.path.exists(main_data_file):
        print(f"\n{'='*70}")
        print("CREATING MAIN DATA TABLE")
        print(f"{'='*70}")
        print(f"\n {main_data_file} not found. Creating joined dataset...")
        
        try:
            # First join demand and metadata using unique_id
            print(f"\n Step 1: Joining demand and metadata on unique_id...")
            conn.execute("""
                CREATE OR REPLACE TEMP TABLE demand_metadata AS
                SELECT 
                    d.*,
                    m.*
                FROM demand d
                INNER JOIN metadata m ON d.unique_id = m.unique_id
            """)
            
            row_count_dm = conn.execute("SELECT COUNT(*) FROM demand_metadata").fetchone()[0]
            print(f"   Joined {row_count_dm:,} rows")
            
            # Then join with weather using timestamp and location_id
            print(f"\n Step 2: Joining with weather on timestamp and location_id...")
            conn.execute("""
                CREATE OR REPLACE TEMP TABLE main_data_temp AS
                SELECT 
                    dm.*,
                    w.*
                FROM demand_metadata dm
                INNER JOIN weather w 
                    ON dm.timestamp = w.timestamp 
                    AND dm.location_id = w.location_id
            """)
            
            row_count_final = conn.execute("SELECT COUNT(*) FROM main_data_temp").fetchone()[0]
            print(f"    Final joined dataset: {row_count_final:,} rows")
            
            # Save to parquet file
            print(f"\n Saving to {main_data_file}...")
            conn.execute(f"""
                COPY main_data_temp TO '{main_data_file}' (FORMAT PARQUET)
            """)
            
            # Verify file was created
            if os.path.exists(main_data_file):
                file_size = os.path.getsize(main_data_file) / (1024 * 1024)  # Size in MB
                print(f"    Successfully saved {main_data_file}")
                print(f"    File size: {file_size:.2f} MB")
                print(f"    Rows: {row_count_final:,}")
            else:
                print(f"     Warning: File may not have been created")
            
            # Also create a table in the database for easy access
            conn.execute("""
                CREATE OR REPLACE TABLE main_data AS
                SELECT * FROM main_data_temp
            """)
            print(f"    Created 'main_data' table in database")
            
        except Exception as e:
            print(f"   Error creating main_data: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n{'='*70}")
        print("MAIN DATA TABLE")
        print(f"{'='*70}")
        print(f"\n {main_data_file} already exists. Loading into database...")
        
        try:
            # Load the existing main_data.parquet into the database
            conn.execute(f"""
                CREATE OR REPLACE TABLE main_data AS 
                SELECT * FROM read_parquet('{main_data_file}')
            """)
            
            row_count = conn.execute("SELECT COUNT(*) FROM main_data").fetchone()[0]
            print(f"    Loaded {row_count:,} rows from {main_data_file}")
            
        except Exception as e:
            print(f"    Error loading main_data: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n💡 You can query the tables using:")
    print(f"   conn = duckdb.connect('data.duckdb')")
    print(f"   result = conn.execute('SELECT * FROM weather LIMIT 10').fetchdf()")
    print(f"   result = conn.execute('SELECT * FROM main_data LIMIT 10').fetchdf()")
    
    return conn


def get_dataset_statistics(db_path='data.duckdb'):
    """Get comprehensive statistics about the dataset"""
    conn = duckdb.connect(db_path)
    
    try:
        print("="*70)
        print("DATASET STATISTICS")
        print("="*70)
        
        # Get all tables
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        stats = {}
        
        for table_name in table_names:
            print(f"\n{'='*70}")
            print(f" TABLE: {table_name.upper()}")
            print(f"{'='*70}")
            
            # Basic info
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
            
            print(f"\n Basic Information:")
            print(f"   Rows:    {row_count:,}")
            print(f"   Columns: {len(columns)}")
            
            # Column details
            print(f"\n Columns:")
            numeric_cols = []
            text_cols = []
            date_cols = []
            
            for col in columns:
                col_name, col_type = col[0], col[1]
                print(f"   - {col_name}: {col_type}")
                
                # Categorize columns
                if 'timestamp' in col_type.lower() or 'date' in col_type.lower():
                    date_cols.append(col_name)
                elif any(t in col_type.lower() for t in ['int', 'double', 'float', 'numeric', 'real']):
                    numeric_cols.append(col_name)
                else:
                    text_cols.append(col_name)
            
            # Date range analysis
            if date_cols:
                print(f"\n Date Range Analysis:")
                for date_col in date_cols:
                    try:
                        date_info = conn.execute(f"""
                            SELECT 
                                MIN({date_col}) as min_date,
                                MAX({date_col}) as max_date,
                                COUNT(DISTINCT {date_col}) as distinct_dates,
                                COUNT(DISTINCT EXTRACT(YEAR FROM {date_col})) as distinct_years,
                                COUNT(DISTINCT EXTRACT(MONTH FROM {date_col})) as distinct_months
                            FROM {table_name}
                        """).fetchone()
                        
                        min_date, max_date, distinct_dates, distinct_years, distinct_months = date_info
                        print(f"   Column: {date_col}")
                        print(f"      Range: {min_date} to {max_date}")
                        print(f"      Distinct dates: {distinct_dates:,}")
                        print(f"      Years: {distinct_years}, Months: {distinct_months}")
                    except Exception as e:
                        print(f"      ⚠️  Could not analyze {date_col}: {str(e)}")
            
            # Numeric column statistics
            if numeric_cols:
                print(f"\n Numeric Column Statistics:")
                for num_col in numeric_cols[:10]:  # Limit to first 10 to avoid too much output
                    try:
                        num_stats = conn.execute(f"""
                            SELECT 
                                COUNT(*) as total,
                                COUNT({num_col}) as non_null,
                                COUNT(*) - COUNT({num_col}) as null_count,
                                MIN({num_col}) as min_val,
                                MAX({num_col}) as max_val,
                                AVG({num_col}) as avg_val,
                                STDDEV({num_col}) as stddev_val,
                                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {num_col}) as median
                            FROM {table_name}
                        """).fetchone()
                        
                        total, non_null, null_count, min_val, max_val, avg_val, stddev_val, median = num_stats
                        null_pct = (null_count / total * 100) if total > 0 else 0
                        
                        print(f"   {num_col}:")
                        print(f"      Non-null: {non_null:,} ({100-null_pct:.1f}%), Null: {null_count:,} ({null_pct:.1f}%)")
                        if non_null > 0:
                            print(f"      Min: {min_val:.4f}, Max: {max_val:.4f}")
                            print(f"      Mean: {avg_val:.4f}, Median: {median:.4f}, StdDev: {stddev_val:.4f}")
                    except Exception as e:
                        print(f"      ⚠️  Could not analyze {num_col}: {str(e)}")
                
                if len(numeric_cols) > 10:
                    print(f"   ... and {len(numeric_cols) - 10} more numeric columns")
            
            # Text/Categorical column statistics
            if text_cols:
                print(f"\n Text/Categorical Column Statistics:")
                for text_col in text_cols[:5]:  # Limit to first 5
                    try:
                        text_stats = conn.execute(f"""
                            SELECT 
                                COUNT(*) as total,
                                COUNT({text_col}) as non_null,
                                COUNT(DISTINCT {text_col}) as distinct_values
                            FROM {table_name}
                        """).fetchone()
                        
                        total, non_null, distinct = text_stats
                        null_count = total - non_null
                        null_pct = (null_count / total * 100) if total > 0 else 0
                        
                        print(f"   {text_col}:")
                        print(f"      Non-null: {non_null:,} ({100-null_pct:.1f}%), Null: {null_count:,} ({null_pct:.1f}%)")
                        print(f"      Distinct values: {distinct:,}")
                        
                        # Show top values if not too many distinct values
                        if distinct <= 20 and distinct > 0:
                            top_values = conn.execute(f"""
                                SELECT {text_col}, COUNT(*) as cnt
                                FROM {table_name}
                                WHERE {text_col} IS NOT NULL
                                GROUP BY {text_col}
                                ORDER BY cnt DESC
                                LIMIT 10
                            """).fetchall()
                            print(f"      Top values:")
                            for val, cnt in top_values:
                                print(f"         '{val}': {cnt:,}")
                    except Exception as e:
                        print(f"      ⚠️  Could not analyze {text_col}: {str(e)}")
                
                if len(text_cols) > 5:
                    print(f"   ... and {len(text_cols) - 5} more text columns")
            
            # Store stats
            stats[table_name] = {
                'row_count': row_count,
                'column_count': len(columns),
                'numeric_columns': numeric_cols,
                'text_columns': text_cols,
                'date_columns': date_cols
            }
        
        # Cross-table relationships
        print(f"\n{'='*70}")
        print(" CROSS-TABLE RELATIONSHIPS")
        print(f"{'='*70}")
        
        # Check unique_id relationships
        if 'demand' in table_names and 'metadata' in table_names:
            try:
                demand_unique_ids = conn.execute("SELECT COUNT(DISTINCT unique_id) FROM demand").fetchone()[0]
                metadata_unique_ids = conn.execute("SELECT COUNT(DISTINCT unique_id) FROM metadata").fetchone()[0]
                
                print(f"\n Unique ID Analysis:")
                print(f"   Demand table unique_ids:  {demand_unique_ids:,}")
                print(f"   Metadata table unique_ids: {metadata_unique_ids:,}")
                
                # Check overlap
                overlap = conn.execute("""
                    SELECT COUNT(DISTINCT d.unique_id)
                    FROM demand d
                    INNER JOIN metadata m ON d.unique_id = m.unique_id
                """).fetchone()[0]
                
                print(f"   Overlapping unique_ids:    {overlap:,}")
                
            except Exception as e:
                print(f"   ⚠️  Could not analyze relationships: {str(e)}")
        
        # Check location_id relationships
        if 'weather' in table_names and 'metadata' in table_names:
            try:
                weather_locations = conn.execute("SELECT COUNT(DISTINCT location_id) FROM weather").fetchone()[0]
                metadata_locations = conn.execute("SELECT COUNT(DISTINCT location_id) FROM metadata").fetchone()[0]
                
                print(f"\n📍 Location ID Analysis:")
                print(f"   Weather table location_ids:  {weather_locations:,}")
                print(f"   Metadata table location_ids: {metadata_locations:,}")
                
            except Exception as e:
                print(f"   ⚠️  Could not analyze location relationships: {str(e)}")
        
        # Summary
        print(f"\n{'='*70}")
        print(" SUMMARY")
        print(f"{'='*70}")
        total_rows = sum(s['row_count'] for s in stats.values())
        total_cols = sum(s['column_count'] for s in stats.values())
        
        print(f"\n   Total tables: {len(stats)}")
        print(f"   Total rows:   {total_rows:,}")
        print(f"   Total columns: {total_cols}")
        
        return stats
        
    except Exception as e:
        print(f" Error getting statistics: {str(e)}")
        return None
    finally:
        conn.close()


def get_building_statistics(db_path='data.duckdb'):
    """Get statistics about buildings: number of buildings, average records per building, records per day"""
    conn = duckdb.connect(db_path)
    
    try:
        print("="*70)
        print("BUILDING STATISTICS")
        print("="*70)
        
        # Number of buildings
        num_buildings = conn.execute("SELECT COUNT(DISTINCT unique_id) FROM demand").fetchone()[0]
        
        # Total number of records
        total_records = conn.execute("SELECT COUNT(*) FROM demand").fetchone()[0]
        
        # Average number of records per building
        avg_records_per_building = total_records / num_buildings if num_buildings > 0 else 0
        
        # Get detailed statistics per building
        building_stats = conn.execute("""
            SELECT 
                unique_id,
                COUNT(*) as record_count,
                MIN(timestamp) as first_record,
                MAX(timestamp) as last_record,
                COUNT(DISTINCT DATE(timestamp)) as distinct_days
            FROM demand
            GROUP BY unique_id
            ORDER BY record_count DESC
        """).fetchdf()
        
        # Calculate statistics from building-level data
        min_records = building_stats['record_count'].min()
        max_records = building_stats['record_count'].max()
        median_records = building_stats['record_count'].median()
        stddev_records = building_stats['record_count'].std()
        
        # Average records per day per building
        avg_records_per_day_per_building = building_stats['record_count'].mean() / building_stats['distinct_days'].mean() if building_stats['distinct_days'].mean() > 0 else 0
        
        # Overall records per day (across all buildings)
        date_range = conn.execute("""
            SELECT 
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date,
                COUNT(DISTINCT DATE(timestamp)) as distinct_days
            FROM demand
        """).fetchone()
        
        min_date, max_date, distinct_days = date_range
        total_days = distinct_days
        avg_records_per_day = total_records / total_days if total_days > 0 else 0
        
        # Records per day per building (average)
        avg_records_per_day_per_building_calc = avg_records_per_building / (building_stats['distinct_days'].mean()) if building_stats['distinct_days'].mean() > 0 else 0
        
        print(f"\n Overall Statistics:")
        print(f"   Total records:           {total_records:,}")
        print(f"   Number of buildings:      {num_buildings:,}")
        print(f"   Date range:              {min_date} to {max_date}")
        print(f"   Total distinct days:     {total_days:,}")
        
        print(f"\n Records per Building:")
        print(f"   Average records/building: {avg_records_per_building:,.2f}")
        print(f"   Min records/building:     {min_records:,.0f}")
        print(f"   Max records/building:     {max_records:,.0f}")
        print(f"   Median records/building:  {median_records:,.0f}")
        print(f"   StdDev records/building:  {stddev_records:,.2f}")
        
        print(f"\n Records per Day:")
        print(f"   Average records/day (total):        {avg_records_per_day:,.2f}")
        print(f"   Average records/day/building:       {avg_records_per_day_per_building:,.2f}")
        
        # Show distribution
        print(f"\n Distribution of Records per Building:")
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            value = building_stats['record_count'].quantile(p / 100)
            print(f"   {p}th percentile: {value:,.0f} records")
        
        # Show top and bottom buildings
        print(f"\n🏆 Top 5 Buildings by Record Count:")
        top_buildings = building_stats.head(5)
        for idx, row in top_buildings.iterrows():
            print(f"   {row['unique_id']}: {row['record_count']:,} records ({row['distinct_days']:,} days)")
        
        print(f"\n📉 Bottom 5 Buildings by Record Count:")
        bottom_buildings = building_stats.tail(5)
        for idx, row in bottom_buildings.iterrows():
            print(f"   {row['unique_id']}: {row['record_count']:,} records ({row['distinct_days']:,} days)")
        
        # Records per day statistics
        daily_stats = conn.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as records_per_day,
                COUNT(DISTINCT unique_id) as buildings_per_day
            FROM demand
            GROUP BY DATE(timestamp)
            ORDER BY date
        """).fetchdf()
        
        avg_daily_records = daily_stats['records_per_day'].mean()
        avg_daily_buildings = daily_stats['buildings_per_day'].mean()
        min_daily_records = daily_stats['records_per_day'].min()
        max_daily_records = daily_stats['records_per_day'].max()
        
        print(f"\n📆 Daily Statistics:")
        print(f"   Average records per day:     {avg_daily_records:,.2f}")
        print(f"   Min records per day:         {min_daily_records:,}")
        print(f"   Max records per day:         {max_daily_records:,}")
        print(f"   Average buildings per day:   {avg_daily_buildings:,.2f}")
        
        return {
            'num_buildings': int(num_buildings),
            'total_records': int(total_records),
            'avg_records_per_building': float(avg_records_per_building),
            'min_records_per_building': int(min_records),
            'max_records_per_building': int(max_records),
            'median_records_per_building': float(median_records),
            'avg_records_per_day': float(avg_records_per_day),
            'avg_records_per_day_per_building': float(avg_records_per_day_per_building),
            'total_days': int(total_days),
            'building_stats': building_stats,
            'daily_stats': daily_stats
        }
        
    except Exception as e:
        print(f" Error getting building statistics: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()


def save_filtered_data_with_year_shift(parquet_file='demand.parquet', output_file='demand_2022_2024.parquet', 
                                       source_years=[2015, 2016, 2017], 
                                       target_years=[2022, 2023, 2024],
                                       use_database=False, db_path='data.duckdb', table_name='demand'):
    """
    Filter data from source years, shift to target years, and save to parquet file
    
    Args:
        parquet_file: Path to input parquet file (default: 'demand.parquet')
        output_file: Output parquet file name
        source_years: List of source years to filter [2015, 2016, 2017]
        target_years: List of target years to shift to [2022, 2023, 2024]
        use_database: If True, read from DuckDB database; if False, read from parquet file
        db_path: Path to DuckDB database (if use_database=True)
        table_name: Table name to process (if use_database=True)
    """
    try:
        print("="*70)
        print("FILTERING AND SHIFTING DATA")
        print("="*70)
        print(f"\n Configuration:")
        print(f"   Source years: {source_years}")
        print(f"   Target years: {target_years}")
        print(f"   Output file: {output_file}")
        
        if use_database:
            # Try to use database (may fail if locked)
            try:
                conn = duckdb.connect(db_path, read_only=True)
                print(f"   Reading from database: {db_path}")
                print(f"   Table: {table_name}")
                
                # Get initial count
                initial_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                print(f"\n Initial record count: {initial_count:,}")
                
                # Build year filter condition
                year_conditions = " OR ".join([f"EXTRACT(YEAR FROM timestamp) = {year}" for year in source_years])
                
                # Get count of filtered records
                filtered_count = conn.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table_name}
                    WHERE {year_conditions}
                """).fetchone()[0]
                
                print(f"\nFiltering data...")
                print(f"   Records matching filter: {filtered_count:,}")
                
                # Fetch the filtered data
                print(f"\n📥 Fetching data from database...")
                filtered_df = conn.execute(f"""
                    SELECT 
                        unique_id,
                        timestamp,
                        y
                    FROM {table_name}
                    WHERE {year_conditions}
                """).fetchdf()
                
                conn.close()
                
            except Exception as db_error:
                print(f"\n⚠️  Database access failed: {str(db_error)}")
                print(f"   Falling back to reading from parquet file: {parquet_file}")
                use_database = False
        
        if not use_database:
            # Use DuckDB to filter parquet file directly (much faster for large files)
            if not os.path.exists(parquet_file):
                print(f"\n Error: Parquet file '{parquet_file}' not found")
                return None
            
            print(f"\n📥 Filtering parquet file using DuckDB: {parquet_file}")
            print(f"   This is more efficient for large files...")
            
            # Use DuckDB in-memory connection to filter parquet directly
            conn = duckdb.connect()
            
            # Build year filter condition
            year_conditions = " OR ".join([f"EXTRACT(YEAR FROM timestamp) = {year}" for year in source_years])
            
            # Get count first
            filtered_count = conn.execute(f"""
                SELECT COUNT(*) 
                FROM read_parquet('{parquet_file}')
                WHERE {year_conditions}
            """).fetchone()[0]
            
            print(f"\n Records matching filter: {filtered_count:,}")
            
            # Build year shift CASE statement for SQL
            year_shift_case = "CASE " + " ".join([
                f"WHEN EXTRACT(YEAR FROM timestamp) = {src} THEN {tgt - src}"
                for src, tgt in zip(source_years, target_years)
            ]) + " ELSE 0 END"
            
            # Write directly to parquet from DuckDB (much faster, no memory overhead)
            print(f"\n Transforming and writing directly to parquet...")
            print(f"   This avoids loading all data into memory...")
            
            conn.execute(f"""
                COPY (
                    SELECT 
                        unique_id,
                        timestamp + INTERVAL ({year_shift_case}) YEAR as timestamp,
                        y
                    FROM read_parquet('{parquet_file}')
                    WHERE {year_conditions}
                ) TO '{output_file}' (FORMAT PARQUET)
            """)
            
            # Get count for verification
            count_result = conn.execute(f"""
                SELECT COUNT(*) 
                FROM read_parquet('{output_file}')
            """).fetchone()[0]
            
            conn.close()
            
            print(f"    Written {count_result:,} records directly to {output_file}")
            
            # Load a small sample to verify and show statistics
            print(f"\n Verifying output file...")
            conn = duckdb.connect()
            sample_df = conn.execute(f"""
                SELECT 
                    MIN(timestamp) as min_date,
                    MAX(timestamp) as max_date,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT EXTRACT(YEAR FROM timestamp)) as distinct_years
                FROM read_parquet('{output_file}')
            """).fetchdf()
            
            year_dist = conn.execute(f"""
                SELECT 
                    EXTRACT(YEAR FROM timestamp) as year,
                    COUNT(*) as count
                FROM read_parquet('{output_file}')
                GROUP BY year
                ORDER BY year
            """).fetchdf()
            
            conn.close()
            
            print(f"   Date range: {sample_df['min_date'].iloc[0]} to {sample_df['max_date'].iloc[0]}")
            print(f"   Total records: {sample_df['total_records'].iloc[0]:,}")
            print(f"   Distinct years: {int(sample_df['distinct_years'].iloc[0])}")
            print(f"\n Year distribution in output:")
            for _, row in year_dist.iterrows():
                print(f"   {int(row['year'])}: {row['count']:,} records")
            
            # Get full count for return value
            record_count = count_result
        
        else:
            # If using database, still need to transform years in pandas
            # Create year mapping dictionary
            year_mapping = dict(zip(source_years, target_years))
            
            # Transform years in pandas
            print(f"\n Shifting years: {year_mapping}")
            
            # Extract year and map it
            filtered_df['year'] = filtered_df['timestamp'].dt.year
            filtered_df['year_shift'] = filtered_df['year'].map(year_mapping)
            
            # Calculate the year difference to add
            filtered_df['year_diff'] = filtered_df['year_shift'] - filtered_df['year']
            
            # Shift the timestamp by the year difference using DateOffset
            transformed_df = filtered_df.copy()
            transformed_df['timestamp'] = transformed_df.apply(
                lambda row: row['timestamp'] + DateOffset(years=int(row['year_diff'])), 
                axis=1
            )
            
            # Keep only the original columns
            transformed_df = transformed_df[['unique_id', 'timestamp', 'y']].copy()
        
        # If we used database path, we still need to save and verify
        if use_database:
            # Verify the transformation
            if len(transformed_df) > 0:
                min_year = transformed_df['timestamp'].dt.year.min()
                max_year = transformed_df['timestamp'].dt.year.max()
                print(f"\n Transformed date range: {transformed_df['timestamp'].min()} to {transformed_df['timestamp'].max()}")
                print(f"   Year range: {min_year} to {max_year}")
                
                # Check year distribution
                year_dist = transformed_df['timestamp'].dt.year.value_counts().sort_index()
                print(f"\n Year distribution in output:")
                for year, count in year_dist.items():
                    print(f"   {year}: {count:,} records")
            
            # Save to parquet
            print(f"\n Saving to {output_file}...")
            transformed_df.to_parquet(output_file, index=False, engine='pyarrow')
            record_count = len(transformed_df)
        else:
            # Already written directly, record_count was set above
            record_count = count_result
        
        # Verify file was created
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # Size in MB
            print(f"\n File saved successfully!")
            print(f"   File size: {file_size:.2f} MB")
            print(f"   Records: {record_count:,}")
        else:
            print(f"   Error: File was not created")
            return None
        
        print(f"\n Process completed successfully!")
        print(f"   Output file: {output_file}")
        
        return {
            'output_file': output_file,
            'record_count': record_count,
            'source_years': source_years,
            'target_years': target_years
        }
        
    except Exception as e:
        print(f" Error processing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def count_records_per_year(parquet_file='demand.parquet', db_path='data.duckdb', 
                           use_database=False, table_name='demand'):
    """
    Count number of records in each year
    
    Args:
        parquet_file: Path to parquet file (if use_database=False)
        db_path: Path to DuckDB database (if use_database=True)
        use_database: If True, read from database; if False, read from parquet
        table_name: Table name (if use_database=True)
    """
    try:
        print("="*70)
        print("RECORD COUNT BY YEAR")
        print("="*70)
        
        if use_database:
            try:
                conn = duckdb.connect(db_path, read_only=True)
                print(f"\n Reading from database: {db_path}")
                print(f"   Table: {table_name}")
                
                # Get record count per year
                year_counts = conn.execute(f"""
                    SELECT 
                        EXTRACT(YEAR FROM timestamp) as year,
                        COUNT(*) as record_count
                    FROM {table_name}
                    GROUP BY year
                    ORDER BY year
                """).fetchdf()
                
                conn.close()
                
            except Exception as db_error:
                print(f"\n⚠️  Database access failed: {str(db_error)}")
                print(f"   Falling back to reading from parquet file: {parquet_file}")
                use_database = False
        
        if not use_database:
            if not os.path.exists(parquet_file):
                print(f"\n Error: Parquet file '{parquet_file}' not found")
                return None
            
            print(f"\n Reading from parquet file: {parquet_file}")
            
            # Use DuckDB to read parquet directly (efficient)
            conn = duckdb.connect()
            
            year_counts = conn.execute(f"""
                SELECT 
                    EXTRACT(YEAR FROM timestamp) as year,
                    COUNT(*) as record_count
                FROM read_parquet('{parquet_file}')
                GROUP BY year
                ORDER BY year
            """).fetchdf()
            
            conn.close()
        
        # Display results
        print(f"\n Record Count by Year:")
        print("-" * 70)
        print(f"{'Year':<10} {'Record Count':<20} {'Percentage':<15}")
        print("-" * 70)
        
        total_records = year_counts['record_count'].sum()
        
        for _, row in year_counts.iterrows():
            year = int(row['year'])
            count = int(row['record_count'])
            percentage = (count / total_records * 100) if total_records > 0 else 0
            print(f"{year:<10} {count:>15,} {percentage:>14.2f}%")
        
        print("-" * 70)
        print(f"{'TOTAL':<10} {total_records:>15,} {100.0:>14.2f}%")
        
        # Additional statistics
        print(f"\n Statistics:")
        print(f"   Total records: {total_records:,}")
        print(f"   Number of years: {len(year_counts)}")
        print(f"   Average records/year: {total_records / len(year_counts):,.0f}")
        print(f"   Min records/year: {year_counts['record_count'].min():,} ({int(year_counts.loc[year_counts['record_count'].idxmin(), 'year'])})")
        print(f"   Max records/year: {year_counts['record_count'].max():,} ({int(year_counts.loc[year_counts['record_count'].idxmax(), 'year'])})")
        
        return {
            'year_counts': year_counts,
            'total_records': int(total_records),
            'num_years': len(year_counts)
        }
        
    except Exception as e:
        print(f" Error counting records per year: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def count_buildings_per_type_per_year(demand_file='demand.parquet', metadata_file='metadata.parquet',
                                      db_path='data.duckdb', use_database=False):
    """
    Count number of buildings per type for each year
    
    Args:
        demand_file: Path to demand parquet file
        metadata_file: Path to metadata parquet file
        db_path: Path to DuckDB database (if use_database=True)
        use_database: If True, read from database; if False, read from parquet files
    """
    try:
        print("="*70)
        print("BUILDING COUNT BY TYPE PER YEAR")
        print("="*70)
        
        if use_database:
            try:
                conn = duckdb.connect(db_path, read_only=True)
                print(f"\n Reading from database: {db_path}")
                
                # Count distinct buildings per type per year
                building_counts = conn.execute("""
                    SELECT 
                        EXTRACT(YEAR FROM d.timestamp) as year,
                        m.building_class as building_type,
                        COUNT(DISTINCT d.unique_id) as building_count
                    FROM demand d
                    INNER JOIN metadata m ON d.unique_id = m.unique_id
                    GROUP BY year, building_type
                    ORDER BY year, building_type
                """).fetchdf()
                
                conn.close()
                
            except Exception as db_error:
                print(f"\n⚠️  Database access failed: {str(db_error)}")
                print(f"   Falling back to reading from parquet files")
                use_database = False
        
        if not use_database:
            if not os.path.exists(demand_file):
                print(f"\n Error: Demand parquet file '{demand_file}' not found")
                return None
            
            if not os.path.exists(metadata_file):
                print(f"\n Error: Metadata parquet file '{metadata_file}' not found")
                return None
            
            print(f"\nReading from parquet files:")
            print(f"   Demand: {demand_file}")
            print(f"   Metadata: {metadata_file}")
            
            # Use DuckDB to join and count
            conn = duckdb.connect()
            
            building_counts = conn.execute(f"""
                SELECT 
                    EXTRACT(YEAR FROM d.timestamp) as year,
                    m.building_class as building_type,
                    COUNT(DISTINCT d.unique_id) as building_count
                FROM read_parquet('{demand_file}') d
                INNER JOIN read_parquet('{metadata_file}') m ON d.unique_id = m.unique_id
                GROUP BY year, building_type
                ORDER BY year, building_type
            """).fetchdf()
            
            conn.close()
        
        if len(building_counts) == 0:
            print(f"\n⚠️  No data found. Check if files exist and have matching unique_ids.")
            return None
        
        # Get all unique years and building types
        years = sorted(building_counts['year'].unique())
        building_types = sorted(building_counts['building_type'].dropna().unique())
        
        print(f"\n Building Count by Type per Year:")
        print("="*100)
        
        # Create a pivot table for better visualization
        pivot_data = building_counts.pivot_table(
            index='building_type',
            columns='year',
            values='building_count',
            fill_value=0
        )
        
        # Display header
        header = f"{'Building Type':<25}"
        for year in years:
            header += f" {int(year):<12}"
        header += f" {'Total':<12}"
        print(header)
        print("-" * 100)
        
        # Display each building type
        type_totals = {}
        for building_type in building_types:
            row = f"{building_type:<25}"
            type_total = 0
            for year in years:
                count = int(pivot_data.loc[building_type, year]) if building_type in pivot_data.index else 0
                row += f" {count:>11,}"
                type_total += count
            row += f" {type_total:>11,}"
            print(row)
            type_totals[building_type] = type_total
        
        # Display year totals
        print("-" * 100)
        year_totals_row = f"{'TOTAL':<25}"
        for year in years:
            year_total = int(building_counts[building_counts['year'] == year]['building_count'].sum())
            year_totals_row += f" {year_total:>11,}"
        grand_total = int(building_counts['building_count'].sum())
        year_totals_row += f" {grand_total:>11,}"
        print(year_totals_row)
        print("="*100)
        
        # Additional statistics
        print(f"\n Summary Statistics:")
        print(f"   Total building-years: {grand_total:,}")
        print(f"   Number of years: {len(years)}")
        print(f"   Number of building types: {len(building_types)}")
        
        print(f"\nBuilding Types:")
        for building_type in building_types:
            avg_per_year = type_totals[building_type] / len(years) if len(years) > 0 else 0
            print(f"   - {building_type}: {type_totals[building_type]:,} total ({avg_per_year:.1f} avg/year)")
        
        # Show year-by-year breakdown
        print(f"\n Year-by-Year Breakdown:")
        for year in years:
            year_data = building_counts[building_counts['year'] == year]
            total_buildings = int(year_data['building_count'].sum())
            print(f"\n   {int(year)}: {total_buildings:,} total buildings")
            for _, row in year_data.iterrows():
                print(f"      {row['building_type']}: {int(row['building_count']):,} buildings")
        
        return {
            'building_counts': building_counts,
            'pivot_table': pivot_data,
            'years': [int(y) for y in years],
            'building_types': list(building_types),
            'type_totals': type_totals
        }
        
    except Exception as e:
        print(f" Error counting buildings per type per year: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_years_in_demand(db_path='data.duckdb'):
    """Get the number of years covered in the demand table"""
    conn = duckdb.connect(db_path)
    
    try:
        # Get min and max timestamps
        result = conn.execute("""
            SELECT 
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date,
                EXTRACT(YEAR FROM MAX(timestamp)) - EXTRACT(YEAR FROM MIN(timestamp)) + 1 as years_span,
                COUNT(DISTINCT EXTRACT(YEAR FROM timestamp)) as distinct_years
            FROM demand
        """).fetchone()
        
        min_date, max_date, years_span, distinct_years = result
        
        print("="*70)
        print("DEMAND TABLE - YEAR ANALYSIS")
        print("="*70)
        print(f"\n Date Range:")
        print(f"   Start: {min_date}")
        print(f"   End:   {max_date}")
        print(f"\n Years:")
        print(f"   Span (inclusive): {int(years_span)} years")
        print(f"   Distinct years:   {int(distinct_years)} years")
        
        # Get list of distinct years
        years_list = conn.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM timestamp) as year
            FROM demand
            ORDER BY year
        """).fetchall()
        
        years = [int(row[0]) for row in years_list]
        print(f"\n Years covered: {', '.join(map(str, years))}")
        
        return {
            'min_date': min_date,
            'max_date': max_date,
            'years_span': int(years_span),
            'distinct_years': int(distinct_years),
            'years_list': years
        }
        
    except Exception as e:
        print(f" Error querying demand table: {str(e)}")
        return None
    finally:
        conn.close()


if __name__ == '__main__':
    # Import parquet files (if needed)
    conn = import_parquet_to_duckdb()
    
    # Get comprehensive dataset statistics
    # stats = get_dataset_statistics()
    
    # Get building statistics
    # building_stats = get_building_statistics()
    
    # Get years in demand table
    # years_info = get_years_in_demand()
    
    # Count records per year
    # year_counts = count_records_per_year()
    
    # Count buildings per type per year
    # building_type_counts = count_buildings_per_type_per_year()
    
    # Save filtered data with year shift (2015-2017 -> 2022-2024)
    # result = save_filtered_data_with_year_shift(
    #     output_file='demand_2022_2024.parquet',
    #     source_years=[2015, 2016, 2017],
    #     target_years=[2022, 2023, 2024]
    # )
    
    # Keep connection open for interactive use
    # if conn:
    #     print(f"\n Database connection is open. Close with: conn.close()")
    #     # Uncomment the line below if you want to close the connection automatically
    #     # conn.close()
