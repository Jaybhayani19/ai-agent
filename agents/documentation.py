# agents/documentation.py
from vertexai.generative_models import GenerativeModel
from db_manager import DBManager
from logger import get_logger
from cache import cache_result, retry_on_failure

logger = get_logger(__name__)

class DocumentationAgent:
    def __init__(self):
        self.db = DBManager()
        self.model = GenerativeModel("gemini-1.5-pro")
    @retry_on_failure
    def _generate_docs(self, code_to_document: str) -> str:
        prompt = f"""
        You are a technical writer. Your task is to generate a clear and concise
        `README.md` file in Markdown format for the following Python code.
        - Explain the purpose of the code.
        - Describe how to run it, if applicable.
        - Document any functions and their parameters.
        - Only output the raw Markdown content for the README.md file.

        Code to document:
        ---
        {code_to_document}
        ---
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error("Could not generate documentation.", extra={"error": str(e)})
            return f"# Error\n\nCould not generate documentation: {e}"

    def execute_task(self, task_id: int, source_code_task_id: int):
        source_task = self.db.query_one("SELECT code FROM tasks WHERE id = %s", (source_code_task_id,))
        if not source_task or not source_task['code']:
            log_context = {"task_id": task_id, "source_task_id": source_code_task_id}
            logger.warning("No source code found for task to document.", extra=log_context)
            self.db.execute("UPDATE tasks SET status = 'failed', output = 'Source code not found' WHERE id = %s", (task_id,))
            return

        log_context = {"task_id": task_id, "source_task_id": source_code_task_id}
        logger.info("Generating documentation.", extra=log_context)
        
        documentation = self._generate_docs(source_task['code'])
        logger.info("Generated documentation.", extra={"task_id": task_id, "doc_length": len(documentation)})

        self.db.execute(
            "UPDATE tasks SET output = %s, status = %s WHERE id = %s",
            (documentation, 'completed', task_id)
        )
        logger.info(f"Task marked as 'completed'.", extra={"task_id": task_id, "status": "completed"})
