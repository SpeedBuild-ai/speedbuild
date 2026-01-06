from speedbuild.frameworks.django.extraction.feature_dependencies import getCodeBlockFromFile
from .parser import PythonBlockParser
from speedbuild.frameworks.django.utils.var_utils import get_assigned_variables


file_path = "/home/attah/Documents/jannis/api/jannis_api/jannis_health/utils/country.py"
parser = PythonBlockParser()

with open(file_path,"r") as file:
    data = file.read()
    chunks = parser.parse_code(data)

# for i in chunks:
#     print(get_assigned_variables(i,True))

feature_code = getCodeBlockFromFile("country",chunks)

print(feature_code)