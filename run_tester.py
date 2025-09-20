# run_tester.py
import vertexai
from agents.tester import TesterAgent
from dotenv import load_dotenv

# --- IMPORTANT ---
# Change this to the ID of the task that the CodeWriterAgent completed.
TASK_TO_TEST = 11 
# ---

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize Vertex AI
    try:
        PROJECT_ID = "ai-engineer-472512" 
        LOCATION = "asia-south1"
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("Vertex AI Initialized.")
    except Exception as e:
        print(f"Error initializing Vertex AI: {e}")
        return

    # Run the agent
    tester = TesterAgent()
    tester.run_tests_for_task(TASK_TO_TEST)

if __name__ == "__main__":
    main()
