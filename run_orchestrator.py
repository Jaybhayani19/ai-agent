# run_orchestrator.py
from agents.orchestrator import ChiefOrchestratorAgent
from db_manager import DBManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# The ID of the project you inserted in the previous step
TEST_PROJECT_ID = 1

def main():
    db = DBManager()
    project = db.query_one("SELECT goal FROM projects WHERE id = %s", (TEST_PROJECT_ID,))

    if not project:
        print(f"Project with ID {TEST_PROJECT_ID} not found.")
        return

    print(f"Found project goal: {project['goal']}")
    print("--- Starting Orchestrator Agent ---")
    
    orchestrator = ChiefOrchestratorAgent()
    orchestrator.plan_and_store_tasks(TEST_PROJECT_ID, project['goal'])

if __name__ == "__main__":
    main()
