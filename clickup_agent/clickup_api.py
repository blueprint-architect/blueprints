import os
import requests
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLICKUP_API_URL = "https://api.clickup.com/api/v2"

def get_clickup_token():
    """Retrieves the ClickUp API token from environment variables."""
    token = os.getenv("CLICKUP_API_TOKEN")
    if not token:
        logger.error("CLICKUP_API_TOKEN environment variable not set.")
        raise ValueError("CLICKUP_API_TOKEN environment variable not set.")
    return token

def get_headers():
    """Returns the authorization headers for ClickUp API requests."""
    return {
        "Authorization": get_clickup_token(),
        "Content-Type": "application/json"
    }

def get_spaces(team_id: str):
    """
    Fetches all Spaces for a given team_id.

    Args:
        team_id (str): The ID of the team (workspace) to fetch spaces from.

    Returns:
        dict: The JSON response from the API containing spaces, or None if an error occurs.
    """
    if not team_id:
        logger.error("Team ID is required to fetch spaces.")
        return None

    url = f"{CLICKUP_API_URL}/team/{team_id}/space?archived=false"
    logger.info(f"Fetching spaces for team ID: {team_id} from {url}")

    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        logger.info(f"Successfully fetched spaces for team ID: {team_id}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching spaces: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred while fetching spaces: {req_err}")
    except ValueError as val_err: # Handles get_clickup_token() error
        logger.error(f"Configuration error: {val_err}")
    return None

if __name__ == '__main__':
    # This is for basic testing of this module if run directly.
    # You would need to set CLICKUP_API_TOKEN and provide a CLICKUP_TEST_TEAM_ID.
    logger.info("Testing clickup_api.py functions...")
    try:
        token = get_clickup_token()
        logger.info(f"ClickUp API Token (first 5 chars): {token[:5]}...")

        test_team_id = os.getenv("CLICKUP_TEST_TEAM_ID")
        if test_team_id:
            logger.info(f"Attempting to fetch spaces for team ID: {test_team_id}...")
            spaces_data = get_spaces(team_id=test_team_id)
            if spaces_data and "spaces" in spaces_data:
                logger.info(f"Found {len(spaces_data['spaces'])} spaces.")
                for space in spaces_data['spaces']:
                    logger.info(f"  - Space Name: {space['name']} (ID: {space['id']})")
            elif spaces_data:
                logger.info(f"Received data but 'spaces' key not found: {spaces_data}")
            else:
                logger.warning("No spaces data returned or an error occurred.")
        else:
            logger.warning("CLICKUP_TEST_TEAM_ID environment variable not set. Skipping get_spaces test.")

    except ValueError as e:
        logger.error(f"Test failed: {e}")
