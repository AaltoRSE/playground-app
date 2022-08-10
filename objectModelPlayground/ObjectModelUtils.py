import os
import os.path
import shutil
import uuid
import logging
from pathlib import Path

def makeFileExecutable(pathFile):
    cmd = "chmod +x " + pathFile
    os.system(cmd)

def runCmd(cmd):
    os.system(cmd)

def fileExists(path):
    return os.path.isfile(path)

def mkdirRecursively(directory):
    logging.info(f"Creating directory {directory}, if it doesn't exist")
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)



def rmdir(directory):
    logging.info("Removing directory %s", directory)
    try:
        shutil.rmtree(directory)
    except OSError as e:
        return e

def getUUID1():
    return str(uuid.uuid1().hex)

def getUUID4():
    return str(uuid.uuid4().hex)
