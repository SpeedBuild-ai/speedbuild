# Execute Command
import os
import sys
from pathlib import Path

from speedbuild.agents.debugCustomizer.newExec import PythonExecutor

home = str(Path.home())
# express_working_dir = os.path.join(home,".sb","environment","express")#"/home/attah/.sb/environment/express/"


def executeCommand(command : str, framework:str,exec_dir:str=None):
    """
    Executes a given shell command using the PythonExecutor.

    Args:
        command (str): The shell command to execute as a string.
        framework (str) : django or express
        exec_dir (str) : where to execute command, default is root directory

    Behavior:
        - Splits the command string into a list of arguments.
        - Determines if the command should be self-exiting based on whether the last argument is "runserver".
        - Executes the command in a specified working directory and environment.
        - Return the standard output and standard error of the executed command.
    """

    # home = str(Path.home())
    env = None
    wkdir = None

    if framework == "django":
        wkdir =  exec_dir #os.path.join(home,".sb","environment","django","speedbuild_project")
        venv_path = os.path.join(exec_dir,"venv")

        if sys.platform == "win32":
            python_path =  os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")

        # Modify environment to use the venv
        env = os.environ.copy()
        env['VIRTUAL_ENV'] = venv_path

        if sys.platform == "win32":
            env['PATH'] = f"{os.path.join(venv_path, 'Scripts')};{env['PATH']}"
        else:
            env['PATH'] = f"{os.path.join(venv_path, 'bin')}:{env['PATH']}"
    elif framework == "express":
        wkdir =  exec_dir #exec_dir if exec_dir else express_working_dir #TODO : change this to be dynamic
    else:
        return
    
    # print("executing command ",command,"\n\n\n\n")
    
    commandExecutor = PythonExecutor()
    command = command.split(" ")

    selfExiting = False if  command[-1] == "runserver" or command[-1] == "dev" else True
    

    try:
        stdout, stderr = commandExecutor.runCommand(command=command,cwd=wkdir,env=env,self_exit=selfExiting)
    except ValueError as err:
        return err


    if command[-1] == "runserver" and len(stderr) == 1:
        stderr = []

    if len(stderr) > 0:
        stderr = "\n".join(stderr)
        return f"Error : {stderr}"
    
    stdout = "\n".join(stdout)
    return f"Command was Successful and exited without error\nstdout : {stdout}"


# if __name__ == "__main__":
#     res = executeCommand("python manage.py test","django","/home/attah/.sb/environment/django/speedbuild_project")
#     print(res)