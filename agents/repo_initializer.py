# agents/repo_initializer.py
from vertexai.generative_models import GenerativeModel
from db_manager import DBManager
from executor import run_in_sandbox
from logger import get_logger
from cache import cache_result, retry_on_failure

logger = get_logger(__name__)

class RepoInitializerAgent:
    def __init__(self):
        self.db = DBManager()
        self.model = GenerativeModel("gemini-1.5-pro")

    @retry_on_failure
    def _generate_command(self, task_description: str) -> str:
        prompt = f"""
        You are an expert in shell commands and git. Based on the following task,
        provide a single, executable shell command to accomplish it.
        - Only output the raw shell command.
        - The command will be run in the project's root directory.
        - For example, if the task is "initialize a git repository and create a readme",
        a good command is "git init && echo '# New Project' > README.md".

        Task: "{task_description}"
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('`', '')
        except Exception as e:
            logger.error("Error generating command with Gemini.", extra={"error": str(e)})
            return f"echo 'Error generating command: {e}'"

    def execute_task(self, task_id: int):
        task = self.db.query_one("SELECT description FROM tasks WHERE id = %s", (task_id,))
        if not task:
            logger.warning("Task not found in DB.", extra={"task_id": task_id})
            return

        log_context = {"task_id": task_id, "description": task['description']}
        logger.info("Executing repo task.", extra=log_context)

        command = self._generate_command(task['description'])
        logger.info("Generated command.", extra={"task_id": task_id, "command": command})
        
        result = run_in_sandbox(command)
        logger.info("Execution result.", extra={"task_id": task_id, "result": result})

        status = 'completed' if result['exit_code'] == 0 else 'failed'
        output = result['stdout'] if status == 'completed' else result['stderr']
        
        self.db.execute(
            "UPDATE tasks SET output = %s, status = %s WHERE id = %s",
            (output, status, task_id)
        )
        logger.info(f"Task marked as '{status}'.", extra={"task_id": task_id, "status": status})
