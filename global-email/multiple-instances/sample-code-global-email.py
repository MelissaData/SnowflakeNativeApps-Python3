"""
Global Email Multiple Instances Sample Job

Usage:
    python path/to/your/script.py --config path/to/your/config.json
"""
from snowflake.snowpark import Session
import argparse
import concurrent.futures
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

# ──────────────────────────────────────────────────────
# Logging setup – writes to console and a file
# ──────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"Multi-Instances-Job_{datetime.now():%Y%m%d_%H%M}.log"

logger = logging.getLogger("Multi-Instances Sample Job")
logger.setLevel(logging.INFO)

_formatter = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

# Console handler
_consoleHandler = logging.StreamHandler()
_consoleHandler.setFormatter(_formatter)
logger.addHandler(_consoleHandler)
# File handler
logger.info(f"Log file: {LOG_FILE}")
_fileHandler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fileHandler.setFormatter(_formatter)
logger.addHandler(_fileHandler)

# ──────────────────────────────────────────────────────
# Parse arguments & load config from JSON
# ──────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Global Email Multiple Instances Sample Job")
parser.add_argument(
    "--config",
    type=Path,
    default=Path(__file__).parent / "sample-code-global-email-config.json",
    help="Path to the JSON config file (default: sample-code-global-email-config.json)",
)
args = parser.parse_args()

CONFIG_PATH = args.config
with open(CONFIG_PATH, encoding="utf-8") as f:
    CONFIG = json.load(f)

WAREHOUSE           = CONFIG["warehouse"]
DATABASE            = CONFIG["database"]
SCHEMA              = CONFIG["schema"]
OPTIONS             = CONFIG["options"]
OUTPUT_TABLE_FIELDS = CONFIG["output_table_fields"]
DUPLICATE_CHECK     = CONFIG["duplicate_check"]
INSTANCES           = CONFIG["instances"]

# ──────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────
def get_session() -> Session:
    return Session.builder.getOrCreate()

def create_schema(session: Session) -> None:
    session.sql(f"USE WAREHOUSE {WAREHOUSE}").collect()
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.{SCHEMA}").collect()
    session.sql(f"USE SCHEMA {DATABASE}.{SCHEMA}").collect()

def run_batch_job(session: Session, job_name: str, instance: dict) -> dict:
    """Run a batch job. Returns timing and row count info."""
    start_time = time.time()
    start_datetime = datetime.now()

    app = instance["app_name"]
    input_table = instance["source_table"]
    output_table_name = instance["output_table_name"]
    output_table_fields = OUTPUT_TABLE_FIELDS
    order = instance["order_by"]
    limit = instance["limit"]

    session.sql(f"USE WAREHOUSE {WAREHOUSE}").collect()
    session.sql(f"USE SCHEMA {DATABASE}.{SCHEMA}").collect()

    logger.info(f"[{job_name}] [{app}] Instance started")
    # Create the temporary input view
    create_view_sql = f"""
    CREATE OR REPLACE TEMPORARY VIEW {app}.CORE.INPUT_RECORDS AS
    SELECT
        DISTINCT
        RECID                       AS RECORDID,
        COALESCE(MY_COL_1, '')      AS IN_FIELD_1,
        COALESCE(MY_COL_2, '')      AS IN_FIELD_2,
        COALESCE(MY_COL_3, '')      AS IN_FIELD_3
    FROM {input_table}
    ORDER BY {order}
    LIMIT {limit}
    """
    session.sql(create_view_sql).collect()

    # Get source table row count
    row_count = session.sql(f"SELECT COUNT(*) AS REC_COUNT FROM {app}.CORE.INPUT_RECORDS").collect()[0]["REC_COUNT"]
    logger.info(f"[{job_name}] [{app}] Source table {input_table}. Row count: {row_count:,}")

    # Call the stored procedure
    call_batch_job_sql = f"""
    CALL {app}.CORE.VERIFY_MULTIPLE_EMAILS(
         LICENSE                => '<REPLACE_WITH_YOUR_LICENSE_KEY>'
        ,INPUT_TABLE_NAME       => TABLE({app}.CORE.INPUT_RECORDS)
        ,OUTPUT_TABLE_NAME      => '{output_table_name}'
        ,OUTPUT_TABLE_FIELDS    => '{output_table_fields}'
        ,OPTIONS                => '{OPTIONS}'
        ,DUPLICATE_CHECK        => '{DUPLICATE_CHECK}'
    )
    """
    result = session.sql(call_batch_job_sql).collect()

    end_time = time.time()
    end_datetime = datetime.now()
    elapsed = end_time - start_time

    logger.info(f"[{job_name}] [{app}] Row count: {row_count}.    Instance elapsed: {timedelta(seconds=int(elapsed))}.    Result: {json.dumps(json.loads(result[0][0]), indent=2)}")
    logger.info(f"[{job_name}] [{app}] Instance ended")

    return {
        "app_name": app,
        "input_table": input_table,
        "output_table": output_table_name,
        "row_count": row_count,
        "start": start_datetime,
        "end": end_datetime,
        "elapsed_seconds": elapsed,
        "result": result,
    }

# ──────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────
def main():
    # Set up schema on initial session
    session = get_session()
    create_schema(session)

    total_start = time.time()
    job_name = "SAMPLE JOB"
    logger.info(f"\n{'='*60}")
    logger.info(f"[{job_name}] [MAIN] Start job")
    logger.info(f"[{job_name}] [MAIN] Instances count: {len(INSTANCES)}")
    total_start = time.time()
    logger.info(f"\n{'='*60}")

    results = []

    # Run batch jobs in parallel across all instances
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(INSTANCES)) as executor:
        futures = {
            executor.submit(run_batch_job, session, job_name, inst): inst["app_name"]
            for inst in INSTANCES
        }
        for future in concurrent.futures.as_completed(futures):
            app_name = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error on {app_name}: {e}")

    total_end = time.time()
    total_elapsed = total_end - total_start
    total_rows = sum(r["row_count"] for r in results)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"[{job_name}] [MAIN] [JOB Summary]")
    logger.info(f"\n{'='*60}")
    for r in results:
        logger.info(f"[{job_name}] [MAIN] [JOB Summary]  {r['app_name']}")
        logger.info(f"[{job_name}] [MAIN] [JOB Summary]    Source:  {r['input_table']}  ({r['row_count']:,} rows)")
        logger.info(f"[{job_name}] [MAIN] [JOB Summary]    Output:  {r['output_table']}")
        logger.info(f"[{job_name}] [MAIN] [JOB Summary]    Elapsed: {timedelta(seconds=int(r['elapsed_seconds']))}")
    logger.info(f"{'─'*60}")
    logger.info(f"[{job_name}] [MAIN] [JOB Summary]   Total instance counts: {len(INSTANCES)}")
    logger.info(f"[{job_name}] [MAIN] [JOB Summary]   Total rows (all instances): {total_rows:,}")
    logger.info(f"[{job_name}] [MAIN] [JOB Summary]   Total elapsed:  {timedelta(seconds=int(total_elapsed))}")
    logger.info(f"[{job_name}] [MAIN] End job")
    logger.info(f"{'='*60}")

    session.close()

if __name__ == "__main__":
    main()