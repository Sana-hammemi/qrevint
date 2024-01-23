import os
from pathlib import Path


py_files = []
root_dir = Path(os.getcwd()).parents[0]
ui = os.listdir(os.path.join(root_dir, "UI"))

# get python files from UI package
for file in ui:
    if file.endswith(".py"):
        py_files.append(os.path.join(root_dir, "UI", file))

# get python files from Classes package
classes = os.listdir(os.path.join(root_dir, "Classes"))

for file in classes:
    if file.endswith(".py"):
        py_files.append(os.path.join(root_dir, "Classes", file))

# set base command and string
base_command = "pylupdate5.exe -verbose "
path_str = " ".join(py_files)

# get list of existing ts files.
ts_path = os.getcwd()
files = []
# Iterate directory updating each file.
for file in os.listdir(ts_path):
    # check only text files
    if file.endswith('.ts'):
        files.append(os.path.basename(file))

        command = base_command + path_str + " -ts " + os.path.basename(file)
        ret = os.system(command)
