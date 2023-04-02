import os
import subprocess
import tempfile
import ctypes
import sys
from urllib import request
import json
import tarfile

# retrieve authentication token from Docker, pulling most recent image
def authenticate(image_name):
    url = f'https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/{image_name}:pull'
    resp = request.urlopen(request.Request(url, method="GET"))
    return json.loads(resp.read(8096).decode("utf-8"))["token"]

# lists all the layers that make up an image, returns as blobs
def fetch_manifest(image_name, token):
    url = f'https://registry.hub.docker.com/v2/library/{image_name}/manifests/latest'
    headers = {'Authorization': f'Bearer {token}'}
    req = request.Request(url, method="GET", headers=headers)
    resp = request.urlopen(req)
    resp = json.loads(resp.read().decode("utf-8"))
    blobs = [layer["blobSum"] for layer in resp["fsLayers"]]
    return blobs

# download each layer and place into temporary directory
def pull_layers(image_name, blobs, token, chroot_dir):
    for blob in blobs:
        url = f'https://registry.hub.docker.com/v2/library/{image_name}/blobs/{blob}'
        headers = {'Authorization': f'Bearer {token}'}
        req = request.Request(url, method="GET", headers=headers)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, f"{blob}.tar"), "wb") as f:
                with request.urlopen(req) as resp:
                    f.write(resp.read())
            for file in os.listdir(temp_dir):
                ff = tarfile.open(os.path.join(temp_dir, file))
                ff.extractall(chroot_dir)

# runs the Docker command after Docker image is extracted
def mydocker_run(image_name, command):
    with tempfile.TemporaryDirectory() as tmp_dir:
        token = authenticate(image_name)
        blobs = fetch_manifest(image_name, token)
        pull_layers(image_name, blobs, token, tmp_dir)
        command = command[command.rfind("/") + 1 :]

        # Use ctypes to call the unshare() function from the C library with the CLONE_NEWPID flag
        libc = ctypes.CDLL(None)
        CLONE_NEWPID = 0x20000000
        libc.unshare.argtypes = [ctypes.c_int]
        libc.unshare(CLONE_NEWPID)
        os.chroot(tmp_dir)

        completed_process = subprocess.run([command,  *args], capture_output=True)
        sys.stdout.buffer.write(completed_process.stdout)
        sys.stderr.buffer.write(completed_process.stderr)
        exit(completed_process.returncode)

if __name__ == '__main__':
    image_name, command, args = sys.argv[2], sys.argv[3], sys.argv[4:]
    mydocker_run(image_name, command)
