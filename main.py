# main.py
import vertexai
from db_manager import DBManager
from logger import get_logger
import concurrent.futures

# Import all the agents
from agents.orchestrator import ChiefOrchestratorAgent
from agents.code_writer import CodeWriterAgent
from agents.repo_initializer import RepoInitializerAgent
from agents.documentation import DocumentationAgent
from agents.api_integrator import APIIntegratorAgent

logger = get_logger(__name__)

def main():
    # --- Configuration ---
    try:
        PROJECT_ID = "ai-engineer-472512" 
        LOCATION = "asia-south1"
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        logger.info("Vertex AI Initialized.", extra={"project_id": PROJECT_ID, "location": LOCATION})
    except Exception as e:
        logger.error("Error initializing Vertex AI", extra={"error": str(e)})
        return

    PROJECT_ID = 1
    PROJECT_GOAL = (
        "Initialize a git repository, then write a Python script to fetch the current "
        "price of Bitcoin from the CoinDesk API and print the USD rate, and finally, "
        "create a README.md file for the project."
    )
    
    db = DBManager()

    # --- 1. Planning Step ---
    logger.info("--- Starting Planning Step ---", extra={"project_id": PROJECT_ID, "goal": PROJECT_GOAL})
    orchestrator = ChiefOrchestratorAgent()
    
    existing_tasks = db.query_all("SELECT id FROM tasks WHERE project_id = %s", (PROJECT_ID,))
    if not existing_tasks:
        orchestrator.plan_and_store_tasks(PROJECT_ID, PROJECT_GOAL)
    else:
        logger.info("Tasks for this project already exist. Skipping planning.")

    # --- 2. Execution Step (Now with Parallelism) ---
    logger.info("--- Starting Parallel Execution Step ---")
    
    # Instantiate all our specialist agents
    agents = {
        "code_writing": CodeWriterAgent(),
        "repo_init": RepoInitializerAgent(),
        "documentation": DocumentationAgent(),
        "api_integration": APIIntegratorAgent()
    }

    # This helper function will contain our routing logic
    def dispatch_task(task):
        task_type = task['task_type']
        task_id = task['id']
        log_context = {"task_id": task_id, "task_type": task_type}
        logger.info("Dispatching task", extra=log_context)
        
        try:
            if task_type == 'documentation':
                # Handle the documentation agent's special requirement
                source_task = db.query_one("SELECT id FROM tasks WHERE project_id = %s AND status = 'completed' AND task_type IN ('code_writing', 'api_integration') ORDER BY id DESC LIMIT 1", (PROJECT_ID,))
                if source_task:
                    agents[task_type].execute_task(task_id, source_task['id'])
                else:
                    raise ValueError("No prior code task found to document.")
            elif task_type in agents:
                agents[task_type].execute_task(task_id)
            else:
                # Default to the general code writer if type is unknown
                agents["code_writing"].execute_task(task_id)
            return f"Task {task_id} completed."
        except Exception as e:
            logger.error("An error occurred during task dispatch.", extra={"task_id": task_id, "error": str(e)})
            db.execute("UPDATE tasks SET status = 'failed', output = %s WHERE id = %s", (f"Dispatch error: {e}", task_id))
            return f"Task {task_id} failed."

    # Fetch all pending tasks that can be run (for simplicity, we assume all pending tasks are ready)
    pending_tasks = db.query_all("SELECT * FROM tasks WHERE project_id = %s AND status = 'pending' ORDER BY id", (PROJECT_ID,))
    
    if pending_tasks:
        # Use a ThreadPoolExecutor to run tasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks to the executor
            future_to_task = {executor.submit(dispatch_task, task): task for task in pending_tasks}
            
            # Wait for tasks to complete and log the results
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    logger.info("Task finished.", extra={"task_id": task['id'], "result": result})
                except Exception as exc:
                    logger.error(f"Task generated an exception.", extra={"task_id": task['id'], "exception": str(exc)})

    logger.info("All tasks have been processed.")


if __name__ == "__main__":
    main()
