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
import base64
import requests
import json

PORT = 5000
PORT = 6080
HOSTNAME = f"http://127.0.0.1:{PORT}"
# HOSTNAME = f"https://playground.ki-lab.nrw"
# HOSTNAME = f"https://dev01.ki-lab.nrw:8443"
# HOSTNAME = f"https://202.61.243.33:{PORT}"

ENDPOINT_SOLUTION = "/deploy_solution"


if __name__ == "__main__":
    # IMGFILE = "imgf0001.jpeg"
    solutionID ="sudokustream44"
    solutionID ="AI4IndustryPilot_v2"
    # solutionID ="ai4industrybroken"
    pathSolutionZips = "../solutionZips/"
    pathSolutionZip = pathSolutionZips + solutionID + "/solution.zip"

    
    with open(pathSolutionZip, 'rb') as f:
        img = f.read()

    encoded_file = base64.b64encode(img)
    encoded_file = str(encoded_file.decode('utf8'))
    username = "tobias.elvermann@iais.fraunhofer.de"

    body = {
        'solution': encoded_file,
        'username': username
    }
    print(f"{HOSTNAME}{ENDPOINT_SOLUTION}")
    response = requests.post(
        f"{HOSTNAME}{ENDPOINT_SOLUTION}", json = body)
    print(response.status_code)
    print(response.text)