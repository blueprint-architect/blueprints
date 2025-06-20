import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskDefinition:
    """
    Represents the definition of a task to be created in ClickUp.
    This class will be expanded to include more details like checklists,
    assignees, tags, due dates, priorities, etc.
    """
    def __init__(self, title: str, description: str = "", list_id: str = None): # list_id is already here
        if not title:
            raise ValueError("Task title cannot be empty.")
        self.title = title
        self.description = description
        self.list_id = list_id  # The ClickUp List ID where the task should be created/logged

        # Future attributes:
        # self.assignees = []
        # self.tags = []
        # self.priority = None
        # self.due_date = None
        # self.checklist_items = []
        logger.info(f"TaskDefinition created: '{self.title}' for List ID: '{self.list_id}'")

    def to_clickup_api_format(self): # Renamed for clarity
        """
        Converts the task definition to the format expected by the ClickUp API
        for task creation.
        """
        task_data = {
            "name": self.title,
            "description": self.description,
            # "assignees": self.assignees,
            # "tags": self.tags,
            # "priority": self.priority,
            # "due_date": self.due_date,
            # "markdown_description": self.description, # if using markdown
        }
        # This data is typically sent to an endpoint like /list/{list_id}/task
        # So list_id itself is not part of this payload usually.
        return task_data

    def get_details_for_logging(self):
        """
        Returns a dictionary of details relevant for logging this task definition.
        """
        return {
            "title": self.title,
            "description": self.description,
            "list_id": self.list_id
            # Add other fields here if they should be logged directly from task_def
        }


def get_daily_prospecting_task_template(customer_name: str, target_list_id: str = "default_prospecting_list") -> TaskDefinition:
    """
    Example function to generate a predefined task structure for daily prospecting.

    Args:
        customer_name (str): The name of the customer for prospecting.
        target_list_id (str): The ClickUp list ID where this task should be created.
                              Defaults to 'default_prospecting_list' as a placeholder.

    Returns:
        TaskDefinition: An instance of TaskDefinition for the daily prospecting task.
    """
    if not customer_name:
        raise ValueError("Customer name cannot be empty for prospecting task.")

    title = f"Daily Prospecting Follow-up: {customer_name}"
    description = (
        f"Task: Follow up with {customer_name} as part of daily prospecting efforts.\n\n"
        f"Key Actions:\n"
        f"1. Review previous interactions with {customer_name}.\n"
        f"2. Send a personalized follow-up email or message.\n"
        f"3. If applicable, attempt a call or schedule one.\n"
        f"4. Update CRM/notes with the outcome.\n\n"
        f"Objective: Move {customer_name} to the next stage or schedule next interaction."
    )

    task_def = TaskDefinition(title=title, description=description, list_id=target_list_id)
    logger.info(f"Generated daily prospecting task template for '{customer_name}' in list '{target_list_id}'")
    return task_def

if __name__ == '__main__':
    logger.info("Testing tasks.py module (updated)...")

    try:
        # Test TaskDefinition
        basic_task = TaskDefinition(title="Test Basic Task", description="This is a basic test task.", list_id="test_list_123")
        logger.info(f"Basic task created: '{basic_task.title}', API format: {basic_task.to_clickup_api_format()}")
        logger.info(f"Basic task logging details: {basic_task.get_details_for_logging()}")

        # Test template function
        prospect_task = get_daily_prospecting_task_template(customer_name="Global Corp Inc.", target_list_id="sales_leads_list_789")
        logger.info(f"Prospect task title: '{prospect_task.title}' for list: '{prospect_task.list_id}'")
        logger.info(f"Prospect task description:\n{prospect_task.description}")
        logger.info(f"Prospect task ClickUp API format: {prospect_task.to_clickup_api_format()}")
        logger.info(f"Prospect task logging details: {prospect_task.get_details_for_logging()}")

        # Test validation
        try:
            TaskDefinition(title="")
        except ValueError as e:
            logger.info(f"Caught expected error for empty title: {e}")

        try:
            get_daily_prospecting_task_template(customer_name="")
        except ValueError as e:
            logger.info(f"Caught expected error for empty customer name: {e}")

    except Exception as e:
        logger.error(f"Error during tasks.py self-test: {e}", exc_info=True)
