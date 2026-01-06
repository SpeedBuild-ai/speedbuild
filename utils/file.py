import os
from pathlib import Path


def getCurrentDjangoFiles(path):
    python_files = [file for file in os.listdir(path) if file.endswith(".py")]
    return python_files


def findFilePath(path,filename):
    "Get files in a directory"
    file_paths = []
    for root, _, files in os.walk(path):
        for file in files:
            # Get the relative path to the base directory
            if filename in file:
                relative_path = os.path.relpath(os.path.join(root, file), path)
                file_paths.append(relative_path)

    return file_paths


def getAbsolutePath(relative_path):
    relative_path = Path(relative_path)
    absolute_path = relative_path.resolve()

    return str(absolute_path)

def get_template_output_path(feature_name):
    user_dir = str(Path.home())
    user_dir = os.path.join(user_dir,".sb_zip")

    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    output_zip = os.path.join(user_dir,f"speed_build_{feature_name}")  # No .zip extension needed

    return output_zip