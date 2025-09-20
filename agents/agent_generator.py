# agents/agent_generator.py
import os
import re
from vertexai.generative_models import GenerativeModel
from db_manager import DBManager
from logger import get_logger

logger = get_logger(__name__)

class AgentGeneratorAgent:
    def __init__(self):
        self.db = DBManager()
        self.model = GenerativeModel("gemini-1.5-pro")

    def _generate_agent_code(self, spec: str, agent_name: str) -> str:
        """Uses an LLM to generate the full Python code for a new agent."""

        # This is a template for the new agent's code. The LLM will fill it in.
        agent_template = """
from db_manager import DBManager
from executor import run_in_sandbox
from logger import get_logger

logger = get_logger(__name__)

class {agent_name}:
    def __init__(self):
        self.db = DBManager()

    def execute_task(self, task_id: int):
        # The AI will generate the logic for this method.
        pass
"""
        prompt = f"""
        You are an expert Python developer who creates autonomous agents. Your task is to write the
        complete Python code for a new agent class based on a provided specification.

        - The agent's class name MUST be: {agent_name}
        - The code MUST be a complete, runnable Python script containing only this single class.
        - The agent should have a primary method `execute_task(self, task_id: int)`.
        - Use the `db_manager` to fetch task details and the `executor` to run commands if needed.
        - Ensure all logic is contained within the class methods.
        - Only output the raw Python code. Do not add explanations or markdown.

        Here is the agent code template to follow:
        ---
        {agent_template.format(agent_name=agent_name)}
        ---

        Here is the specification for the new agent you must create:
        ---
        {spec}
        ---
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('```python', '').replace('```', '').strip()
        except Exception as e:
            logger.error("Error generating agent code with Gemini.", extra={"error": str(e)})
            return f"# Error generating code: {e}"

    def create_new_agent(self, spec: str):
        """Main method to create, save, and register a new agent."""

        # Ask the LLM to suggest a good BASE name from the spec (e.g., Weather, FileSorter)
        naming_prompt = f"Based on the following agent specification, suggest a short, single-word PascalCase class name. For example, for 'An agent that gets the weather', a good name is 'Weather'. Only output the name. Specification: {spec}"
        try:
            response = self.model.generate_content(naming_prompt)
            # Clean up the name and remove the word Agent if the AI adds it anyway
            base_name = response.text.strip().replace("Agent", "")

            # Simple validation for the base name
            if not re.match(r'^[A-Z][a-zA-Z0-9]+$', base_name):
                raise ValueError(f"Invalid base name generated: {base_name}")

            # --- THE FIX: Programmatically ensure the name ends with 'Agent' ---
            agent_name = f"{base_name}Agent"

        except Exception as e:
            logger.error("Failed to generate a valid agent name.", extra={"error": str(e)})
            return

        logger.info(f"Generated agent name: {agent_name}")

        # Generate the agent's code
        agent_code = self._generate_agent_code(spec, agent_name)

        # Save the code to a new file
        # Use a regex to convert PascalCase to snake_case for the filename
        file_name_base = re.sub(r'(?<!^)(?=[A-Z])', '_', agent_name).lower()
        file_path = os.path.join("agents", f"{file_name_base}.py")

        try:
            with open(file_path, "w") as f:
                f.write(agent_code)
            logger.info(f"Successfully saved new agent code to {file_path}")
        except IOError as e:
            logger.error(f"Failed to write agent file.", extra={"path": file_path, "error": str(e)})
            return

        # Register the new agent in the database
        self.db.execute(
            "INSERT INTO agents (name, description) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
            (agent_name, spec)
        )
        logger.info(f"Registered {agent_name} in the database.", extra={"agent_name": agent_name})

