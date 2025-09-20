# executor.py
import docker
import os
import tempfile
import shutil

def run_in_sandbox(command: str, files: dict = None) -> dict:
    """
    Runs a command inside our custom, pre-configured Docker container using a
    more robust, step-by-step method to ensure output is captured.
    """
    client = docker.from_env()
    temp_dir = tempfile.mkdtemp()
    container = None  # Initialize container to None

    try:
        if files:
            for filename, content in files.items():
                with open(os.path.join(temp_dir, filename), "w") as f:
                    f.write(content)
        
        volume_mount = {os.path.abspath(temp_dir): {'bind': '/app', 'mode': 'rw'}}
        shell_command = ['/bin/sh', '-c', command]

        # Step 1: Create the container
        container = client.containers.create(
            image="metamorph-tester",
            command=shell_command,
            working_dir="/app",
            volumes=volume_mount,
            mem_limit="256m"
        )

        # Step 2: Start the container
        container.start()

        # Step 3: Wait for the container to finish and get the exit code
        result = container.wait()
        exit_code = result['StatusCode']

        # Step 4: Explicitly fetch the logs
        stdout_bytes = container.logs(stdout=True, stderr=False)
        stderr_bytes = container.logs(stdout=False, stderr=True)
        
        stdout = stdout_bytes.decode('utf-8', errors='ignore').strip()
        stderr = stderr_bytes.decode('utf-8', errors='ignore').strip()
        
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code
        }

    except Exception as e:
        return {"stdout": "", "stderr": f"An unexpected executor error: {str(e)}", "exit_code": -1}
    finally:
        # Step 5: Ensure the container is removed
        if container:
            try:
                container.remove()
            except docker.errors.NotFound:
                pass # Container was already removed, which is fine
        
        # Step 6: Ensure the temporary directory is removed
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
