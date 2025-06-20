from flask import Flask, jsonify, request
import logging
import clickup_api  # Direct import
import db           # Direct import
import tasks        # Direct import

app = Flask(__name__)

# Configure basic logging for the app
# Ensure this is done before any logging calls if not handled by Flask's default/basicConfig.
# A common practice is to configure logging once at the application's entry point.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the database when the app module is loaded.
try:
    logger.info("Attempting to initialize database from app.py...")
    db.initialize_database()
    logger.info("Database initialization check complete from app.py.")
except Exception as e:
    logger.critical(f"CRITICAL: Database initialization failed during app startup: {e}", exc_info=True)
    # Depending on desired behavior, you might want to raise e to stop the app
    # or allow it to run (routes using the DB would likely fail).

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
                return jsonify({"warning": "Data fetched, but 'spaces' key not found in response.", "data": spaces_data}), 200

            logger.info(f"Successfully retrieved {len(spaces_data.get('spaces', []))} spaces for team_id: {team_id}")
            return jsonify(spaces_data), 200
        else:
            logger.error(f"Failed to get spaces for team_id: {team_id}. clickup_api.get_spaces returned None.")
            return jsonify({"error": "Failed to retrieve spaces from ClickUp. Check server logs for details."}), 500

    except ValueError as ve:
        logger.error(f"Configuration error (e.g., API token not set) for /get_spaces: {ve}")
        return jsonify({"error": str(ve)}), 400
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
        task_description = data.get('description', "")
        task_list_id = data.get('list_id')

        if not task_title:
            logger.warning(f"/log_task_test: Missing required field: title. Received: {data}")
            return jsonify({"error": "Missing required field: title"}), 400
        if not task_list_id:
             logger.warning(f"/log_task_test: Missing required field: list_id. Received: {data}")
             return jsonify({"error": "Missing required field: list_id for this endpoint"}), 400

        task_def = tasks.TaskDefinition(
            title=task_title,
            description=task_description,
            list_id=task_list_id
        )

        log_details = task_def.get_details_for_logging()

        db_id = db.log_task_event(
            clickup_task_id="LOCAL_TASK_NO_API_ID",
            list_id=log_details['list_id'],
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
    # When running with `python -m clickup_agent.app` from the parent directory:
    # - CLICKUP_API_TOKEN environment variable needs to be set for /get_spaces.
    # - The server will run on 0.0.0.0:5001 by default.
    # - The clickup_agent.db SQLite file will be created in the clickup_agent directory.
    app.run(debug=True, host='0.0.0.0', port=5001)
