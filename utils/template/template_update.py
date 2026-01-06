import os
import re
import shutil


def checkTemplateForVersionUpdate(template_path):
    # TODO : compare extracted feature file to check if feature changed
    return
    if os.path.exists(template_path):
        # print("Template already exist")
        templateIsSame = compare_zip_code_folders(f"{template_path}.zip",os.path.join(template_path, "lts.zip"))

        if templateIsSame:
            os.remove(f"{template_path}.zip") #template did not change, so delete extracted feature
        else:
            next_version = get_next_version_file(template_path)

            #rename old lts version
            last_version_name = os.path.join(template_path,next_version) #new name for last version (current lts version)
            os.rename(os.path.join(template_path, "lts.zip"),last_version_name)

            #move update template to folder
            shutil.move(f"{template_path}.zip", os.path.join(template_path, "lts.zip"))

    else:
        # print("Fresh template")
        # make template base folder
        os.makedirs(template_path, exist_ok=True)

        # move extracted to new folder and rename to lts.zip
        shutil.move(f"{template_path}.zip", os.path.join(template_path, "lts.zip"))


def get_next_version_file(folder_path):

    version_pattern = re.compile(r'^(\d+(?:\.\d+)?)\.zip$')
    versions = []

    for fname in os.listdir(folder_path):
        if fname == "lts.zip":
            continue
        match = version_pattern.match(fname)
        if match:
            ver_str = match.group(1)
            parts = ver_str.split('.')
            if len(parts) == 1:
                major = int(parts[0])
                minor = 0
            else:
                major = int(parts[0])
                minor = int(parts[1])
            versions.append((major, minor))

    if not versions:
        return "0.1.zip"

    # Find highest version
    versions.sort()
    major, minor = versions[-1]

    # Calculate next version
    if minor < 9:
        next_major = major
        next_minor = minor + 1
    else:
        next_major = major + 1
        next_minor = 0

    next_version = f"{next_major}.{next_minor}.zip" if next_minor > 0 else f"{next_major}.zip"
    return next_version