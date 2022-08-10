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