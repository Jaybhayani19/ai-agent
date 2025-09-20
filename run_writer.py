# run_writer.py
import vertexai
from agents.code_writer import CodeWriterAgent
from dotenv import load_dotenv

# --- IMPORTANT ---
# Change this to the ID of the task you just created.
TASK_TO_RUN = 11 
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
    writer = CodeWriterAgent()
    writer.execute_task(TASK_TO_RUN)

if __name__ == "__main__":
    main()
