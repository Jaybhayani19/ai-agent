# test_executor.py
from executor import run_in_sandbox
import time

print("--- Test 1: Successful Execution ---")
# This code should run successfully.
code_success = 'print("Hello from inside the sandbox!")'
result_success = run_in_sandbox(code_success)
print(result_success)

# Add a small delay between tests
time.sleep(1) 

print("\n--- Test 2: Execution with an Error ---")
# This code will raise a ZeroDivisionError, causing a non-zero exit code.
code_error = 'print(1 / 0)'
result_error = run_in_sandbox(code_error)
print(result_error)
