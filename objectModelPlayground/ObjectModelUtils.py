# ===================================================================================
# Copyright (C) 2019 Fraunhofer Gesellschaft. All rights reserved.
# ===================================================================================
# This Graphene software file is distributed by Fraunhofer Gesellschaft
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END==========================================================
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
