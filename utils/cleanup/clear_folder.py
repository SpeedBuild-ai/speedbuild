import os
import shutil



def clear_folder(folder_path):
    """
    Clear all contents of a specified folder, removing files, symlinks, and subdirectories.

    Args:
        folder_path (str): Path to the folder to be cleared.

    Returns:
        None

    Raises:
        OSError: If there are permission issues or other OS-level errors when deleting files.
        FileNotFoundError: If the specified folder path does not exist.

    Examples:
        >>> clear_folder('/path/to/folder')
        # All contents of the folder will be deleted
    """
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) or os.path.islink(file_path):  
            os.remove(file_path)  # Delete files & symlinks
        elif os.path.isdir(file_path):  
            shutil.rmtree(file_path)  # Delete directories