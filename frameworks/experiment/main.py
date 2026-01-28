import os
import asyncio
from speedbuild.frameworks.django.extraction.write_dependency import OneStep
from speedbuild.utils.django.var_utils import get_assigned_variables
from speedbuild.utils.parsers.javascript_typescript.jsParser import JsTxParser
from speedbuild.frameworks.express.extraction.extractCodeJs import extractFeatureCode
from speedbuild.utils.parsers.python.parser import PythonBlockParser

nest_project_root_path = "/home/attah/Documents/work/DBMS/dbms"
flask_project_root = "/home/attah/Documents/python_flask/FlaskIntroduction"

parser = JsTxParser()
python_parser = PythonBlockParser()

async def extract_code(target:str, filePath:str) -> None:
    full_path = os.path.join(nest_project_root_path,filePath)
    output = await extractFeatureCode(target,full_path,nest_project_root_path,"test_output_python")
    print(output)

def extract_flask(target:str, filePath:str) -> None:
    OneStep(file_path=filePath,feature=target,project_root=flask_project_root,folders_in_project_root=[],output_dir="test_flask",project_name="flask")


if __name__ == "__main__":
    # asyncio.run(extract_code("ProgramsService","src/programs/programs.service.ts"))
    extract_flask("delete","/home/attah/Documents/python_flask/FlaskIntroduction/app.py")
