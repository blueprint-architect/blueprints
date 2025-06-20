import sqlite3
import logging
import os
from datetime import datetime

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the database file path within the clickup_agent directory
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: # Fallback for environments where __file__ might not be defined (e.g. some test runners)
    BASE_DIR = os.getcwd()

DATABASE_NAME = 'clickup_agent.db'
DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_NAME)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Access columns by name
        logger.debug(f"Successfully connected to database: {DATABASE_PATH}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database {DATABASE_PATH}: {e}")
        raise

def initialize_database():
    """
    Initializes the database by creating necessary tables if they don't exist.
    """
    schema_v1 = """
    CREATE TABLE IF NOT EXISTS task_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clickup_task_id TEXT,
        list_id TEXT,
        task_name TEXT,
        status TEXT, -- e.g., 'CREATED', 'API_ERROR', 'LOGGED'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        details TEXT -- For storing additional info or error messages
    );

    CREATE TABLE IF NOT EXISTS app_config (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Trigger to update 'updated_at' timestamp on row update for task_log
    CREATE TRIGGER IF NOT EXISTS update_task_log_updated_at
    AFTER UPDATE ON task_log
    FOR EACH ROW
    BEGIN
        UPDATE task_log SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

    -- Trigger to update 'updated_at' timestamp on row update for app_config
    CREATE TRIGGER IF NOT EXISTS update_app_config_updated_at
    AFTER UPDATE ON app_config
    FOR EACH ROW
    BEGIN
        UPDATE app_config SET updated_at = CURRENT_TIMESTAMP WHERE key = OLD.key;
    END;
    """

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(schema_v1)
            conn.commit()
            logger.info(f"Database initialized successfully. Tables ensured to exist at {DATABASE_PATH}")

            cursor.execute("INSERT OR IGNORE INTO app_config (key, value, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                           ('default_clickup_list_id', '', 'Default ClickUp List ID for new tasks', datetime.utcnow(), datetime.utcnow()))
            conn.commit()
            logger.info("Default app_config values ensured.")

    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during database initialization: {e}")
        raise

def log_task_event(clickup_task_id: str, list_id: str, task_name: str, status: str, details: str = ""):
    """
    Logs a task event to the task_log table.
    """
    sql = """
    INSERT INTO task_log (clickup_task_id, list_id, task_name, status, details, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            current_time = datetime.utcnow()
            cursor.execute(sql, (clickup_task_id, list_id, task_name, status, details, current_time, current_time))
            conn.commit()
            logger.info(f"Task event logged: ClickUp ID {clickup_task_id}, Name: {task_name}, Status: {status}")
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Error logging task event for ClickUp ID {clickup_task_id}: {e}")
        return None

def get_task_log_by_clickup_id(clickup_task_id: str):
    """Retrieves a task log entry by its ClickUp Task ID."""
    sql = "SELECT * FROM task_log WHERE clickup_task_id = ?"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (clickup_task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving task log for ClickUp ID {clickup_task_id}: {e}")
        return None

def get_all_task_logs(limit: int = 100):
    """Retrieves all task logs, ordered by creation date, with a limit."""
    sql = "SELECT * FROM task_log ORDER BY created_at DESC LIMIT ?"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all task logs: {e}")
        return []

def set_config_value(key: str, value: str, description: str = ""):
    """Sets or updates a configuration value in the app_config table."""
    sql = """
    INSERT INTO app_config (key, value, description, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
        value = excluded.value,
        description = CASE WHEN excluded.description = '' THEN description ELSE excluded.description END,
        updated_at = excluded.updated_at
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            current_time = datetime.utcnow()
            # Ensure description is not None for the call
            current_description = description if description is not None else ''
            cursor.execute(sql, (key, value, current_description, current_time, current_time))
            conn.commit()
            logger.info(f"Config value set for key '{key}'.")
            return True
    except sqlite3.Error as e:
        logger.error(f"Error setting config value for key '{key}': {e}")
        return False

def get_config_value(key: str):
    """Retrieves a configuration value by its key."""
    sql = "SELECT value FROM app_config WHERE key = ?"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving config value for key '{key}': {e}")
        return None

if __name__ == '__main__':
    print(f"Database will be created at: {DATABASE_PATH}")
    logger.info("Initializing database for testing db.py...")
    initialize_database()

    logger.info("\n--- Testing Config Functions ---")
    set_config_value("test_key_1", "value_1", "Description for key 1")
    logger.info(f"Retrieved 'test_key_1': {get_config_value('test_key_1')}")
    set_config_value("test_key_1", "value_1_updated", "Updated description for key 1") # With description
    logger.info(f"Updated 'test_key_1': {get_config_value('test_key_1')}")
    set_config_value("test_key_2", "value_2_no_desc") # Without description
    logger.info(f"Retrieved 'test_key_2' (no initial desc): {get_config_value('test_key_2')}")
    set_config_value("test_key_2", "value_2_updated", "Now with description")
    logger.info(f"Updated 'test_key_2' (now with desc): {get_config_value('test_key_2')}")


    default_list_id_key = 'default_clickup_list_id'
    logger.info(f"Initial '{default_list_id_key}': {get_config_value(default_list_id_key)}")
    set_config_value(default_list_id_key, 'list123abc', 'My main project list ID')
    logger.info(f"Updated '{default_list_id_key}': {get_config_value(default_list_id_key)}")


    logger.info("\n--- Testing Task Logging ---")
    log_id1 = log_task_event(
        clickup_task_id="cu_task_001",
        list_id="cu_list_alpha",
        task_name="Automated Task Alpha",
        status="CREATED_IN_DB",
        details="Logged via db.py test script"
    )
    if log_id1:
        logger.info(f"Logged task event, local DB ID: {log_id1}")

    log_id2 = log_task_event(
        clickup_task_id="cu_task_002",
        list_id="cu_list_beta",
        task_name="Automated Task Beta",
        status="ERROR_API_RESPONSE",
        details="Simulated API error during logging test"
    )
    if log_id2:
        logger.info(f"Logged task event, local DB ID: {log_id2}")

    logger.info("\n--- Retrieving Task Logs ---")
    task_log_entry = get_task_log_by_clickup_id("cu_task_001")
    if task_log_entry:
        logger.info(f"Retrieved log for cu_task_001: {task_log_entry['task_name']}, Status: {task_log_entry['status']}")
    else:
        logger.warning("Could not retrieve log for cu_task_001")

    all_logs = get_all_task_logs(5)
    logger.info(f"Retrieved {len(all_logs)} task logs:")
    for i, log_entry in enumerate(all_logs):
        logger.info(f"  Log {i+1}: ID={log_entry['id']}, ClickUpID={log_entry['clickup_task_id']}, Name={log_entry['task_name']}, Status={log_entry['status']}, LoggedAt={log_entry['created_at']}")

    logger.info("\n--- db.py testing complete ---")
