# agents/tester.py
import vertexai
from vertexai.generative_models import GenerativeModel
from db_manager import DBManager
from executor import run_in_sandbox

class TesterAgent:
    """
    Takes the code from a task, generates pytest tests, runs them in a sandbox,
    and updates the database with the test status.
    """
    def __init__(self):
        self.db = DBManager()
        self.model = GenerativeModel("gemini-1.5-pro")

    def _generate_test_code(self, code_to_test: str) -> str:
        """Uses an LLM to generate pytest code."""
        prompt = f"""
        You are a senior software quality assurance engineer. Your task is to write a pytest test file
        for the given Python code.
        - The code to be tested will be in a file named 'main.py'.
        - Your test code will be in a file named 'test_main.py'. 
        - Inside each test function, you explicitly called `main.main()` function to run the code being tested
        - For the success case, test the side-effects (e.g., a file is created with the correct content).
        - **For the failure case, you MUST use the 'mocker' fixture from 'pytest-mock' to simulate an error.** For example, use 'mocker.patch("builtins.open")' to make the 'open' function raise an IOError. This is more reliable than changing file permissions.
        - You MUST use the 'capsys' fixture to capture and check for the printed error message in the failure case.
        - Only output the raw Python code for the 'test_main.py' file. Do not include explanations or markdown.

        Code to test:
        ---
        {code_to_test}
        ---
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('```python', '').replace('```', '').strip()
        except Exception as e:
            print(f"Error generating test code with Gemini: {e}")
            return "" # Return empty if test generation fails

    def run_tests_for_task(self, task_id: int):
        """The main method to generate and run tests for a given task."""
        task = self.db.query_one("SELECT code FROM tasks WHERE id = %s", (task_id,))
        if not task or not task['code']:
            print(f"No code found for task {task_id} to test.")
            self.db.execute("UPDATE tasks SET test_status = 'no_code' WHERE id = %s", (task_id,))
            return

        print(f"Generating tests for task {task_id}...")
        test_code = self._generate_test_code(task['code'])
        print("--- Generated Test Code ---\n" + test_code)

        if not test_code:
            print("LLM failed to generate test code.")
            self.db.execute("UPDATE tasks SET test_status = 'generation_failed' WHERE id = %s", (task_id,))
            return

        # Prepare the files for the sandbox
        files = {
            'main.py': task['code'],
            'test_main.py': test_code
        }
        
        # Command to install pytest and run it
        command = "pytest -v --junitxml=report.xml; exit_code=$?; cat report.xml; exit $exit_code"

        print("Running tests in sandbox...")
        result = run_in_sandbox(command, files)
        
        print("--- Test Execution Result ---\n", result)

        # Determine status and update the database
        test_status = 'pass' if result['exit_code'] == 0 else 'fail'
        
        self.db.execute(
            "UPDATE tasks SET test_status = %s WHERE id = %s",
            (test_status, task_id)
        )
        print(f"Task {task_id} test status updated to '{test_status}'.")
