from db_manager import DBManager
from executor import run_in_sandbox
from logger import get_logger
import requests

logger = get_logger(__name__)

class OpenMeteoWeatherAgent:
    def __init__(self):
        self.db = DBManager()

    def execute_task(self, task_id: int):
        task_description = self.db.get_task_description(task_id)
        try:
            latitude, longitude = self._parse_coordinates(task_description)
        except ValueError as e:
            logger.error(f"Failed to parse coordinates: {e}")
            return

        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            temperature = data['current_weather']['temperature']
            print(f"Current temperature: {temperature}°C")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
        except KeyError as e:
            logger.error(f"Error parsing weather data: Missing key {e}")


    def _parse_coordinates(self, task_description: str):
        parts = task_description.split("latitude", 1)
        if len(parts) != 2:
            raise ValueError("Invalid task description: 'latitude' not found.")
        
        lat_part = parts[1].split(",", 1)
        if len(lat_part) != 2:
            raise ValueError("Invalid task description: Latitude and longitude not separated by comma.")

        try:
            latitude = float(lat_part[0].strip())
        except ValueError:
            raise ValueError("Invalid latitude format.")

        lon_part = lat_part[1].split("longitude", 1)
        if len(lon_part) != 2:
            raise ValueError("Invalid task description: 'longitude' not found after latitude.")

        try:
            longitude = float(lon_part[1].strip())
        except ValueError:
            raise ValueError("Invalid longitude format.")
        
        return latitude, longitude