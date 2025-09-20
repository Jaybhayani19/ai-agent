# agents/api_integrator.py
from vertexai.generative_models import GenerativeModel
from db_manager import DBManager
from executor import run_in_sandbox
from logger import get_logger
from cache import cache_result, retry_on_failure

logger = get_logger(__name__)

class APIIntegratorAgent:
    def __init__(self):
        self.db = DBManager()
        self.model = GenerativeModel("gemini-1.5-pro")
    @retry_on_failure
    def _generate_code(self, task_description: str) -> str:
        prompt = f"""
        You are an expert Python developer specializing in API integration.
        Write a complete Python script to accomplish the following task.
        - The script will be executed in a sandboxed environment.
        - It MUST use the `requests` library for any HTTP calls.
        - It should handle potential errors and print a clear message if the API call fails.
        - All logic must be wrapped in a `main()` function, called by a standard
          `if __name__ == "__main__":` block.
        - Only output the raw Python code.

        Task: "{task_description}"
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('```python', '').replace('```', '').strip()
        except Exception as e:
            logger.error("Error generating code with Gemini.", extra={"error": str(e)})
            return f"print('Error generating code: {e}')"

    def execute_task(self, task_id: int):
        task = self.db.query_one("SELECT description FROM tasks WHERE id = %s", (task_id,))
        if not task:
            logger.warning("Task not found in DB.", extra={"task_id": task_id})
            return
            
        log_context = {"task_id": task_id, "description": task['description']}
        logger.info("Executing API task.", extra=log_context)

        generated_code = self._generate_code(task['description'])
        logger.info("Generated code for API task.", extra={"task_id": task_id, "code_length": len(generated_code)})

        files = {'main.py': generated_code}
        command = "pip install -q requests && python main.py"
        
        result = run_in_sandbox(command, files, network_enabled=True)
        logger.info("Execution result for API task.", extra={"task_id": task_id, "result": result})

        status = 'completed' if result['exit_code'] == 0 else 'failed'
        output = result['stdout'] if status == 'completed' else result['stderr']
        
        self.db.execute(
            "UPDATE tasks SET code = %s, output = %s, status = %s WHERE id = %s",
            (generated_code, output, status, task_id)
        )
        logger.info(f"Task marked as '{status}'.", extra={"task_id": task_id, "status": status})
