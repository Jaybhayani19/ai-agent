# agents/orchestrator.py
import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from db_manager import DBManager
from cache import cache_result, retry_on_failure
from logger import get_logger

logger = get_logger(__name__)

class ChiefOrchestratorAgent:
    def __init__(self):
        self.db = DBManager()

    @cache_result(ttl_seconds=86400)
    @retry_on_failure
    def _call_llm_for_planning(self, goal: str) -> dict | None:
        """Calls the Vertex AI Gemini API to get a categorized project plan."""
        prompt = f"""
        You are an expert software project manager. Break down the following high-level goal
        into a series of specific, ordered, and actionable tasks. For each task, you must
        also assign a `task_type` from a specific list.

        The output must be a valid JSON object containing a single key "tasks", which is an array of objects.
        
        Each object in the "tasks" array must have:
        1. "task_id": A unique integer for this plan, starting from 1.
        2. "description": A clear, concise command for another agent to execute.
        3. "dependencies": An array of 'task_id's that must be completed before this task can start.
        4. "task_type": The category of the task. Must be one of the following strings:
           - "repo_init": For tasks like initializing a git repository.
           - "documentation": For tasks related to writing a README.md or other documentation.
           - "api_integration": For tasks that involve fetching data from a third-party API.
           - "code_writing": For general Python code that doesn't fit other categories.

        Goal: "{goal}"
        """
        try:
            model = GenerativeModel("gemini-1.5-pro")
            generation_config = GenerationConfig(response_mime_type="application/json")
            response = model.generate_content(prompt, generation_config=generation_config)
            return json.loads(response.text)
        except Exception as e:
            logger.error("Error calling Vertex AI API or parsing JSON.", extra={"error": str(e), "goal": goal})
            return None

    def plan_and_store_tasks(self, project_id: int, goal: str):
        plan = self._call_llm_for_planning(goal)
        if not plan or 'tasks' not in plan:
            logger.error("Failed to generate a valid plan from the LLM.", extra={"project_id": project_id, "goal": goal})
            return

        task_count = len(plan['tasks'])
        logger.info(f"Generated {task_count} categorized tasks. Storing in database...", extra={"project_id": project_id, "task_count": task_count})
        
        for task in plan['tasks']:
            dependencies_json = json.dumps(task.get('dependencies', []))
            task_type = task.get('task_type', 'general')
            
            self.db.execute(
                """
                INSERT INTO tasks (project_id, description, dependencies, task_type, status)
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (project_id, task['description'], dependencies_json, task_type)
            )
        logger.info("All tasks have been successfully stored in the database.", extra={"project_id": project_id})
