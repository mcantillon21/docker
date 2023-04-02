import os
import subprocess
import tempfile
import shutil
import ctypes
import sys

def authenticate(image_name):
    url = f'https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/{image_name}:pull'
    response = requests.get(url)
    token = response.json()['access_token']
    return token

def fetch_manifest(image_name, token):
    url = f'https://registry.hub.docker.com/v2/library/{image_name}/manifests/latest'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    manifest = response.json()
    return manifest

def pull_layers(image_name, manifest, chroot_dir):
    layers = manifest['layers']
    for layer in layers:
        layer_hash = layer['digest']
        layer_file = os.path.join(chroot_dir, f'{layer_hash}.tar')
        url = f'https://registry.hub.docker.com/v2/library/{image_name}/blobs/{layer_hash}'
        response = requests.get(url)
        with open(layer_file, 'wb') as f:
            f.write(response.content)
        subprocess.run(['tar', '-C', chroot_dir, '-xvf', layer_file])

def run_command(chroot_dir, command):
    os.makedirs(os.path.join(chroot_dir, os.path.dirname(command).strip("/")))
    shutil.copy(command, os.path.join(chroot_dir, command.strip("/")))
    os.chroot(chroot_dir)

    # Use ctypes to call the unshare() function from the C library with the CLONE_NEWPID flag
    libc = ctypes.CDLL(None)
    CLONE_NEWPID = 0x20000000
    libc.unshare.argtypes = [ctypes.c_int]
    libc.unshare(CLONE_NEWPID)

    completed_process = subprocess.run([command])
    exit(completed_process.returncode)

def mydocker_run(image_name, command):
    chroot_dir = tempfile.mkdtemp()
    token = authenticate(image_name)
    manifest = fetch_manifest(image_name, token)
    pull_layers(image_name, manifest, chroot_dir)
    run_command(chroot_dir, command)

if __name__ == '__main__':
    import requests
    image_name, command = sys.argv[1], sys.argv[2:]
    mydocker_run(image_name, command)
