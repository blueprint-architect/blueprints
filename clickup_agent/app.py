from flask import Flask, jsonify, request
import logging
# Adjusted import to work when 'clickup_agent' is a package
from . import clickup_api
from . import db
from . import tasks
# If running 'python app.py' from within 'clickup_agent' directory and
# 'clickup_agent' is not installed/PYTHONPATH not set, this might need adjustment.
# Using `from . import clickup_api` is standard for intra-package imports.

app = Flask(__name__)

# Configure basic logging for the app (if not already comprehensively done)
# Ensure this is done before any logging calls.
if not app.logger.handlers: # Avoid adding multiple handlers if already configured
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # If using Flask's app.logger, you might configure it differently
    # For simplicity, ensuring basicConfig is called if no handlers exist.
else: # Assuming logger might be configured by Flask or another part of the app
    pass # Use existing logger configuration

logger = logging.getLogger(__name__) # Get the logger instance for this module


# Initialize the database
# This will run once when the app module is loaded.
try:
    logger.info("Attempting to initialize database from app.py...")
    db.initialize_database() # This is the key line to add
    logger.info("Database initialization check complete from app.py.")
except Exception as e:
    # Using app.logger or the root logger for critical errors if specific logger not yet fully configured
    logging.critical(f"CRITICAL: Database initialization failed during app startup: {e}", exc_info=True)
    # Consider how to handle this: raise the exception to stop app, or try to continue?
    # For now, it logs and continues, but routes using DB might fail.
    # raise e # Option: re-raise to prevent app from starting with a faulty DB setup

@app.route('/')
def hello_world():
    return 'Hello, ClickUp Agent!'

@app.route('/get_spaces/<team_id>', methods=['GET'])
def get_team_spaces(team_id: str):
    """
    Endpoint to fetch and display ClickUp Spaces for a given team_id.
    Requires CLICKUP_API_TOKEN to be set in the environment.
    """
    logger.info(f"Received request for /get_spaces for team_id: {team_id}")
    try:
        spaces_data = clickup_api.get_spaces(team_id=team_id)

        if spaces_data:
            if 'err' in spaces_data and spaces_data['err']:
                 logger.error(f"ClickUp API returned an error: {spaces_data['err']}")
                 return jsonify({"error": "ClickUp API error", "details": spaces_data['err']}), 500

            if "spaces" not in spaces_data:
                logger.warning(f"Spaces data for team {team_id} fetched but 'spaces' key is missing: {spaces_data}")
                # This could be a valid response if the team has no spaces, or API changed.
                # ClickUp usually returns an empty list: {"spaces": []}
                # So, if 'spaces' key is missing entirely, it's more of an unexpected structure.
                return jsonify({"warning": "Data fetched, but 'spaces' key not found in response.", "data": spaces_data}), 200

            logger.info(f"Successfully retrieved {len(spaces_data.get('spaces', []))} spaces for team_id: {team_id}")
            return jsonify(spaces_data), 200
        else:
            # This case handles if get_spaces returns None (e.g., token error, request exception logged in clickup_api)
            logger.error(f"Failed to get spaces for team_id: {team_id}. clickup_api.get_spaces returned None.")
            return jsonify({"error": "Failed to retrieve spaces from ClickUp. Check server logs for details."}), 500

    except ValueError as ve:
        logger.error(f"Configuration error (e.g., API token not set) for /get_spaces: {ve}")
        return jsonify({"error": str(ve)}), 400 # 400 for client-side configuration issue
    except Exception as e:
        logger.exception(f"An unexpected error occurred in /get_spaces for team_id {team_id}: {e}")
        return jsonify({"error": "An unexpected server error occurred"}), 500

@app.route('/log_task_test', methods=['POST'])
def log_task_test_route():
    """
    Test endpoint to create a TaskDefinition from POSTed JSON data
    and log it to the database. Does not create a task in ClickUp.
    Expects JSON: {"title": "...", "description": "...", "list_id": "..."}
    """
    logger.info("Received request for /log_task_test")

    try:
        data = request.get_json()
        if not data:
            logger.warning("/log_task_test: Missing or invalid JSON payload.")
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        task_title = data.get('title')
        task_description = data.get('description', "") # Optional
        task_list_id = data.get('list_id')

        if not task_title: # list_id can be None for TaskDefinition, but let's require for logging here
            logger.warning(f"/log_task_test: Missing required field: title. Received: {data}")
            return jsonify({"error": "Missing required field: title"}), 400
        if not task_list_id: # Enforcing list_id for this test logging endpoint
             logger.warning(f"/log_task_test: Missing required field: list_id. Received: {data}")
             return jsonify({"error": "Missing required field: list_id for this endpoint"}), 400


        # Create a TaskDefinition instance
        task_def = tasks.TaskDefinition(
            title=task_title,
            description=task_description,
            list_id=task_list_id
        )

        log_details = task_def.get_details_for_logging()

        db_id = db.log_task_event(
            clickup_task_id="LOCAL_TASK_NO_API_ID", # Placeholder as no real CU task created
            list_id=log_details['list_id'], # This comes from task_def now
            task_name=log_details['title'],
            status="LOGGED_VIA_TEST_ENDPOINT",
            details=f"Description: {log_details['description']}"
        )

        if db_id:
            logger.info(f"Task '{task_def.title}' logged to DB with id: {db_id} via /log_task_test")
            return jsonify({
                "message": "Task logged successfully in database",
                "db_id": db_id,
                "logged_details": log_details
            }), 201
        else:
            logger.error(f"Failed to log task '{task_def.title}' to database via /log_task_test.")
            return jsonify({"error": "Failed to log task to database"}), 500

    except tasks.ValueError as ve:
        logger.error(f"/log_task_test: Validation error creating TaskDefinition: {ve}")
        return jsonify({"error": f"Task definition error: {str(ve)}"}), 400
    except Exception as e:
        logger.exception(f"An unexpected error occurred in /log_task_test: {e}")
        return jsonify({"error": "An unexpected server error occurred"}), 500

if __name__ == '__main__':
    # To run this directly using `python clickup_agent/app.py`:
    # 1. Ensure CLICKUP_API_TOKEN is set in your environment.
    # 2. Provide a CLICKUP_TEST_TEAM_ID if you want to test the /get_spaces endpoint via browser/curl.
    #
    # The `from . import clickup_api` should work if Python recognizes `clickup_agent` as a package
    # (which the __init__.py helps with) and you run it contextually.
    # For robust execution, running as a module `python -m clickup_agent.app` from parent directory
    # is often preferred after development.

    # Example: To allow running `python app.py` from inside `clickup_agent` directory
    # and have `from . import clickup_api` work correctly, no special sys.path manipulation
    # is typically needed if __init__.py is present.

    app.run(debug=True, host='0.0.0.0', port=5001)
