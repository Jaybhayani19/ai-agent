# agents/code_writer.py
import vertexai
from vertexai.generative_models import GenerativeModel
from db_manager import DBManager
from executor import run_in_sandbox

class CodeWriterAgent:
    """
    Takes a task, generates Python code, executes it in a sandbox,
    and updates the database with the results.
    """
    def __init__(self):
        self.db = DBManager()
        # Initialize the Gemini model
        self.model = GenerativeModel("gemini-1.5-pro")

    def _generate_code(self, task_description: str) -> str:
        """Uses the LLM to generate Python code for a given task."""
        prompt = f"""
        You are a senior Python developer. Write a complete Python script to accomplish the following task.
        - The script will be executed in a sandboxed environment with no network access.
        - **Crucially, all of your logic must be wrapped in a `main()` function.**
        - **You must include the standard `if __name__ == "__main__":` block to call the `main()` function.**
        - Only output the raw Python code. Do not add explanations or markdown.

        Task: "{task_description}"
        """
        try:
            response = self.model.generate_content(prompt)
            # Clean up the response to ensure it's raw code
            return response.text.strip().replace('```python', '').replace('```', '').strip()
        except Exception as e:
            print(f"Error generating code with Gemini: {e}")
            return f"print('Error generating code: {e}')" # Return a printable error

    def execute_task(self, task_id: int):
        """Fetches, codes, executes, and updates a single task."""
        task = self.db.query_one("SELECT description FROM tasks WHERE id = %s", (task_id,))
        if not task:
            print(f"Task {task_id} not found.")
            return

        print(f"Executing task {task_id}: {task['description']}")
        
        # 1. Generate Code
        generated_code = self._generate_code(task['description'])
        print("--- Generated Code ---\n" + generated_code)

        # 2. Execute Code in Sandbox
        # Prepare the code as a file for the executor
        files = {'main.py': generated_code}

        # Prepare the command to execute that file with the Python interpreter
        command = "python main.py"

        # Run the command in the sandbox
        result = run_in_sandbox(command, files)
        print("--- Execution Result ---\n", result)

        # 3. Update Database
        status = 'completed' if result['exit_code'] == 0 else 'failed'
        output = result['stdout'] if status == 'completed' else result['stderr']
        
        self.db.execute(
            """
            UPDATE tasks
            SET code = %s, output = %s, status = %s
            WHERE id = %s
            """,
            (generated_code, output, status, task_id)
        )
        print(f"Task {task_id} marked as '{status}'.")
