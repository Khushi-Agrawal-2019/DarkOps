"""
Return Detective — BigQuery Data Loader
Loads Parquet tables from data/out/ into BigQuery dataset 'return_detective'.
Also provides a DuckDB local mirror for offline and local testing.
"""

import os
import glob
from dotenv import load_dotenv
import duckdb

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "")
DATASET = os.getenv("BIGQUERY_DATASET", "return_detective")
OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
DUCKDB_PATH = os.path.join(OUT_DIR, "return_detective.duckdb")

def load_to_duckdb():
    """Always maintains a local high-performance DuckDB copy of all parquet files."""
    print("🦆 Syncing Parquet tables to local DuckDB analytical database...")
    con = duckdb.connect(DUCKDB_PATH)
    parquet_files = glob.glob(os.path.join(OUT_DIR, "*.parquet"))
    for pf in parquet_files:
        table_name = os.path.splitext(os.path.basename(pf))[0]
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{pf}')")
        cnt = con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        print(f"  ✓ DuckDB {table_name}: {cnt:,d} rows")
    con.close()
    print(f"✓ Local DuckDB synced to {DUCKDB_PATH}")

def load_to_bigquery():
    """Uploads Parquet tables to BigQuery if GCP credentials are configured."""
    if not PROJECT_ID or PROJECT_ID == "your-gcp-project-id":
        print("ℹ️  GCP PROJECT_ID not configured in .env; skipping remote BigQuery load.")
        print("   Local DuckDB analytical engine will serve queries for development.")
        return

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID)
        print(f"☁️  Uploading tables to BigQuery dataset `{PROJECT_ID}.{DATASET}`...")
        
        parquet_files = glob.glob(os.path.join(OUT_DIR, "*.parquet"))
        for pf in parquet_files:
            table_name = os.path.splitext(os.path.basename(pf))[0]
            table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"
            
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.PARQUET,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )
            
            with open(pf, "rb") as source_file:
                job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
            job.result()
            loaded_table = client.get_table(table_ref)
            print(f"  ✓ BigQuery {table_ref}: {loaded_table.num_rows:,d} rows")
        print("✅ BigQuery dataset successfully populated!")
    except Exception as e:
        print(f"⚠️  BigQuery upload skipped or failed: {e}")
        print("   Continuing with local analytical store.")

if __name__ == "__main__":
    load_to_duckdb()
    load_to_bigquery()
