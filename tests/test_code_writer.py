# tests/test_code_writer.py
import pytest
from agents.code_writer import CodeWriterAgent

def test_execute_task_success(mocker):
    """
    Tests the happy path of the CodeWriterAgent's execute_task method.
    It verifies that the agent correctly processes a task and updates the
    database with a 'completed' status.
    """
    # 1. Setup the Mocks
    # Mock the database manager
    mock_db_instance = mocker.MagicMock()
    mock_db_instance.query_one.return_value = {'description': 'Create a hello world script.'}
    mocker.patch('agents.code_writer.DBManager', return_value=mock_db_instance)

    # Mock the Gemini model's response
    mock_gemini_response = mocker.MagicMock()
    mock_gemini_response.text = "print('Hello, World!')"
    mock_gemini_model_instance = mocker.MagicMock()
    mock_gemini_model_instance.generate_content.return_value = mock_gemini_response
    mocker.patch('agents.code_writer.GenerativeModel', return_value=mock_gemini_model_instance)
    
    # Mock the sandbox executor's response
    mock_executor_result = {'stdout': 'Hello, World!', 'stderr': '', 'exit_code': 0}
    mocker.patch('agents.code_writer.run_in_sandbox', return_value=mock_executor_result)

    # 2. Instantiate and Run the Agent
    code_writer_agent = CodeWriterAgent()
    code_writer_agent.execute_task(task_id=1)

    # 3. Assert the Results
    # Verify that the database was queried for the correct task
    mock_db_instance.query_one.assert_called_once_with("SELECT description FROM tasks WHERE id = %s", (1,))

    # Verify that the final database update was called with the correct status
    mock_db_instance.execute.assert_called_once()
    # Get the arguments of the call to check them
    update_args = mock_db_instance.execute.call_args[0]
    update_status = update_args[1][2] # The status is the 3rd element in the params tuple
    assert update_status == 'completed'
