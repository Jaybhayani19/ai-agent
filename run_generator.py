# run_generator.py
import vertexai
from dotenv import load_dotenv
from agents.agent_generator import AgentGeneratorAgent
from logger import get_logger

logger = get_logger(__name__)

def main():
    # --- Configuration ---
    load_dotenv()
    try:
        PROJECT_ID = "ai-engineer-472512" 
        LOCATION = "asia-south1"
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        logger.info("Vertex AI Initialized.")
    except Exception as e:
        logger.error("Error initializing Vertex AI", extra={"error": str(e)})
        return

    # --- Define the new agent we want to create ---
    AGENT_SPECIFICATION = (
        "An agent that gets the current weather for a given location (latitude and longitude). "
        "It should use the Open-Meteo API (api.open-meteo.com) which does not require an API key. "
        "The execute_task method should take a task description like 'Get weather for latitude 52.52, longitude 13.41'. "
        "It needs to parse the latitude and longitude, call the API, and print the current temperature in Celsius."
    )

    # --- Run the generator ---
    generator = AgentGeneratorAgent()
    generator.create_new_agent(AGENT_SPECIFICATION)

if __name__ == "__main__":
    main()
