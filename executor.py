# executor.py
import docker
import os
import tempfile
import shutil

def run_in_sandbox(command: str, files: dict = None, network_enabled: bool = False) -> dict:
    """
    Runs a command inside our custom, pre-configured Docker container.
    """
    client = docker.from_env()
    container = None

    try:
        temp_dir = tempfile.mkdtemp()
        if files:
            for filename, content in files.items():
                with open(os.path.join(temp_dir, filename), "w") as f:
                    f.write(content)

        volume_mount = {os.path.abspath(temp_dir): {'bind': '/app', 'mode': 'rw'}}
        shell_command = ['/bin/sh', '-c', command]

        # Create the container, now with the network_disabled flag
        container = client.containers.create(
            image="metamorph-tester",
            command=shell_command,
            working_dir="/app",
            volumes=volume_mount,
            mem_limit="256m",
            network_disabled=(not network_enabled) # <-- ADD THIS LINE
        )

        # Start, wait, and get logs
        container.start()
        result = container.wait()
        exit_code = result['StatusCode']

        stdout_bytes = container.logs(stdout=True, stderr=False)
        stderr_bytes = container.logs(stdout=False, stderr=True)

        stdout = stdout_bytes.decode('utf-8', errors='ignore').strip()
        stderr = stderr_bytes.decode('utf-8', errors='ignore').strip()

        return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}

    except Exception as e:
        return {"stdout": "", "stderr": f"An unexpected executor error: {str(e)}", "exit_code": -1}
    finally:
        if container:
            try:
                container.remove()
            except docker.errors.NotFound:
                pass 

        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
