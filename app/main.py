import requests
import sys
import tempfile
import shutil
import os
import tarfile

def main():

    # Parse command-line arguments
    image_name = sys.argv[3]
    command = sys.argv[4:]
    
    # Authenticate with Docker Hub
    auth_endpoint = "https://auth.docker.io/token"
    auth_data = {
        "service": "registry.docker.io",
        "scope": "repository:{image_name}:pull".format(image_name=image_name)
    }
    auth_headers = {
        "Accept": "application/json"
    }
    auth_response = requests.get(auth_endpoint, params=auth_data, headers=auth_headers)
    auth_token = auth_response.json()["token"]
    print(auth_token)
    
    # Fetch image manifest
    manifest_endpoint = "https://registry.hub.docker.com/v2/{image_name}/manifests/latest".format(image_name=image_name)
    manifest_headers = {
        "Authorization": "Bearer {auth_token}".format(auth_token=auth_token),
        "Accept": "application/vnd.docker.distribution.manifest.v2+json"
    }
    manifest_response = requests.get(manifest_endpoint, headers=manifest_headers)
    manifest_json = manifest_response.json()
    
    # Pull layers of image and extract to chroot directory
    temp_dir = tempfile.mkdtemp()
    layer_dir = os.path.join(temp_dir, "layers")
    os.makedirs(layer_dir)
    for layer in manifest_json["layers"]:
        layer_digest = layer["digest"]
        layer_endpoint = "https://registry.hub.docker.com/v2/{image_name}/blobs/{layer_digest}".format(
            image_name=image_name, layer_digest=layer_digest)
        layer_headers = {
            "Authorization": "Bearer {auth_token}".format(auth_token=auth_token),
            "Accept": "application/vnd.docker.image.rootfs.diff.tar.gzip"
        }
        layer_response = requests.get(layer_endpoint, headers=layer_headers, stream=True)
        layer_tar = tarfile.open(fileobj=layer_response.raw, mode="r|gz")
        layer_tar.extractall(layer_dir)
        layer_tar.close()
        
    # Copy command into chroot directory
    command_dir = os.path.join(temp_dir, "command")
    os.makedirs(command_dir)
    shutil.copy(command[0], os.path.join(command_dir, os.path.basename(command[0])))
    
    # Change root to chroot directory and execute command
    os.chroot(temp_dir)
    os.execv(os.path.join(command_dir, os.path.basename(command[0])), command)

if __name__ == "__main__":
    main()
