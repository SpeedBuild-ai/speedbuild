import os
from speedbuild.sb import extractFeature

project_path = "/home/attah/Documents/jannis/api/jannis_api"
file_name = "shop/views.py"
target = "ManageSupplements"

extracted_file = extractFeature(project_path,[
    "speedbuild",
    "extract",
    target,
    file_name,
    "--django"
],True)

print(extracted_file)