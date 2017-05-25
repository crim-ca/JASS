import fnmatch
import os

destPath = os.path.dirname(os.path.realpath(__file__))
rootModule = "jass"


def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

def get_ignore_modules_config(rootModuleDirectory):
    filesPaths = find_files(rootModuleDirectory,"*.py")
    notProjectModuleNames = {}
    # staring with import
    for f in filesPaths:
        content = open(f).read()
        for record in content.split('\n'):
            if record.startswith("import ") or record.startswith("from "):
                try:
                    mod = record.split(" ")[1].split(" ")[0]
                    if mod[0] in ".":
                        mod = mod[1:] 
                    if mod[0] in ".":
                        mod = mod[1:]
                    currentMod = ""
                    for modParts in mod.split("."):
                        currentMod =currentMod + "." + modParts
                        if currentMod[0] in ".":
                            currentMod = currentMod[1:]
                        notProjectModuleNames[currentMod] = 1
                except:
                    """
                    Happens if you import from . as an example
                    """
    
    for f in filesPaths:
        moduleName = os.path.splitext(os.path.basename(f))[0]
        if moduleName in notProjectModuleNames:
            del notProjectModuleNames[moduleName]
    
    # remove existing reserved modules
    for moduleName in ["os","sys","unittest","random","datetime","optparse","re","collections","logging","configparser","traceback","httplib"]:
        if moduleName in notProjectModuleNames:
            del notProjectModuleNames[moduleName]
    
    notProjectModuleNamesArr =list(notProjectModuleNames.keys()) 
    
    notProjectModuleNamesArr = [x for x in notProjectModuleNamesArr if x]
    ignoreModuleForConfig = '["{0}"]'.format('","'.join(notProjectModuleNamesArr))
        
    strToAppendToConfig="# -*- coding: utf-8 -*-\nimport sys\nfrom mock import Mock as MagicMock\n\nclass Mock(MagicMock):\n    __all__ = []\n    @classmethod\n    def __getattr__(cls, name):\n        return Mock()\n\nMOCK_MODULES = "
    strToAppendToConfig = strToAppendToConfig + ignoreModuleForConfig + "\nsys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)\n"
    return strToAppendToConfig

def update_config_and_build_doc(projectPath,rootModule):
    """
    :param projectPath: path to the project for which to build the docs
    :param rootModule: the root python module containing all python source code needed to be documented
    """
    # update sphinx docs
    os.chdir(projectPath)
    # print "Entering{0}".format(projectPath)
    os.system("rm -rf {0}/docs/*".format(projectPath))

    # Files to exclude from building in documentation. 
    # The files need to be added to exclude_patterns in configs/sphinx_config.py
    os.system("sphinx-apidoc -F -o docs {0}/ setup.py create_db_if_not_exist.py builddoc.py".format(projectPath))
    
    #Copying original sphinx configuration to docs module.
    os.system("cp -a {0}/configs/sphinx-conf.py {0}/docs/conf.py".format(projectPath))
    
    with file("{0}/docs/conf.py".format(projectPath), 'r') as original: 
        data = original.read()
    
    stringToAppend = get_ignore_modules_config(os.path.join(projectPath,rootModule))
    
    with file("{0}/docs/conf.py".format(projectPath), 'w') as modified: 
        modified.write(stringToAppend + data)
    
    # Files to exclude from building in documentation. 
    # The files need to be added to exclude_patterns in configs/sphinx_config.py
    os.chdir(projectPath +"/docs")
    os.system("make html")

# get the latest info from git
os.system("git pull")
update_config_and_build_doc(destPath,rootModule)
