# agents/orchestrator.py
import os
import json
import vertexai # <-- New import
from vertexai.generative_models import GenerativeModel, GenerationConfig
from db_manager import DBManager

# --- SOLUTION: Explicitly initialize Vertex AI with your project and location ---
try:
    # Find your project ID by running 'gcloud config get-value project' in your terminal
    PROJECT_ID = "ai-engineer-472512"  # <-- Your Google Cloud Project ID
    LOCATION = "asia-south1"      # <-- Your region, e.g., "asia-south1"

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"Vertex AI initialized for project {PROJECT_ID} in {LOCATION}")

except Exception as e:
    print(f"Error initializing Vertex AI: {e}")
    exit()


class ChiefOrchestratorAgent:
    """
    Uses the Vertex AI Gemini API to create a detailed, step-by-step plan.
    """
    def __init__(self):
        self.db = DBManager()

    def _call_llm_for_planning(self, goal: str) -> dict | None:
        """Calls the Vertex AI Gemini API to get a project plan."""
        prompt = f"""
        Break down the following high-level software development goal into a series of specific,
        ordered, and actionable tasks. The output must be a valid JSON object containing a single key "tasks",
        which is an array of objects.
        
        Each object in the "tasks" array must have:
        1. "task_id": A unique integer for this plan, starting from 1.
        2. "description": A clear, concise command for another agent to execute.
        3. "dependencies": An array of 'task_id's that must be completed before this task can start. An empty array [] means it has no dependencies.

        Goal: "{goal}"
        """
        
        try:
            # Using a stable model name is generally better than a specific version
            model = GenerativeModel("gemini-1.5-pro")
            
            generation_config = GenerationConfig(
                response_mime_type="application/json"
            )

            response = model.generate_content(prompt, generation_config=generation_config)
            
            return json.loads(response.text)
        
        except Exception as e:
            print(f"Error calling Vertex AI API or parsing JSON: {e}")
            return None

    def plan_and_store_tasks(self, project_id: int, goal: str):
        """Plans the entire task structure for a given goal and saves it to the DB."""
        plan = self._call_llm_for_planning(goal)

        if not plan or 'tasks' not in plan:
            print("Failed to generate a valid plan from the LLM.")
            return

        print(f"Generated {len(plan['tasks'])} tasks. Storing in database...")
        for task in plan['tasks']:
            dependencies_json = json.dumps(task['dependencies'])
            
            self.db.execute(
                """
                INSERT INTO tasks (project_id, description, dependencies, status)
                VALUES (%s, %s, %s, 'pending')
                """,
                (project_id, task['description'], dependencies_json)
            )
        print("All tasks have been successfully stored in the database.")
