from fastapi import FastAPI, File, UploadFile, HTTPException
import hashlib
import os
import tarfile
import subprocess
from signal import SIGTERM

app = FastAPI()

# Define a global variable to store the PID of the running process
running_process = None

@app.post("/upload/")
async def create_upload_file(file: UploadFile):
    global running_process

    # If a process is running, terminate it
    if running_process:
        os.kill(running_process.pid, SIGTERM)
        running_process = None

    # Step 1: Generate a hash of the uploaded file and create a new directory
    file_bytes = file.file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    extract_folder = f"/tmp/{file_hash}"
    os.makedirs(extract_folder, exist_ok=True)
    
    # Step 2: Save and extract the uploaded file
    file_location = f"/tmp/{file_hash}/{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        file_object.write(file_bytes)

    with tarfile.open(file_location, "r:gz") as tar:
        tar.extractall(path=extract_folder)
    
    # Step 3: Find the .galleon directory and set working_dir
    working_dir = None
    for root, dirs, files in os.walk(extract_folder):
        if ".galleon" in dirs:
            working_dir = root
            break

    if working_dir is None:
        raise HTTPException(status_code=400, detail="No .galleon directory found")
    
    # Step 4: Check for custom setup instructions
    galleon_dir = os.path.join(working_dir, ".galleon")
    setup_file = None
    run_file = None

    if "setup.sh" in os.listdir(galleon_dir):
        setup_file = "setup.sh"
    elif "setup.py" in os.listdir(galleon_dir):
        setup_file = "setup.py"
    
    if "run.sh" in os.listdir(galleon_dir):
        run_file = "run.sh"
    elif "run.py" in os.listdir(galleon_dir):
        run_file = "run.py"

    # Step 5: Set the environment variable
    os.environ["GALLEON_PORT"] = "15788"

    # Step 6: Perform setup and run the app
    if setup_file:
        subprocess.call([os.path.join(galleon_dir, setup_file)])
        if run_file:
            running_process = subprocess.Popen([os.path.join(galleon_dir, run_file), "--galleon-port", "15788"])
        return
    
    requirements_path = os.path.join(working_dir, "requirements.txt")
    environment_path = os.path.join(working_dir, "environment.yml")

    if os.path.exists(requirements_path):
        subprocess.call(["pip", "install", "-r", requirements_path])
    elif os.path.exists(environment_path):
        # Prefer micromamba over mamba for environment setup
        if os.system("command -v micromamba") == 0:
            subprocess.call(["micromamba", "shell", "init", "-s", "bash", "-p", os.environ["HOME"]])
            subprocess.call(["micromamba", "install", "-f", environment_path, "--prefix", os.environ["CONDA_PREFIX"]])
        elif os.system("command -v mamba") == 0:
            subprocess.call(["mamba", "install", "-f", environment_path, "--prefix", os.environ["CONDA_PREFIX"]])
        else:
            subprocess.call(["conda", "install", "-f", environment_path, "--prefix", os.environ["CONDA_PREFIX"]])

    app_path = os.path.join(working_dir, "app.py")
    
    if os.path.exists(app_path):
        # Run the app in the current environment
        running_process = subprocess.Popen(["python", app_path, "--port", "15788"])
    else:
        raise HTTPException(status_code=400, detail="No app.py found in working directory")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=15781)
