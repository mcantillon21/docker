import subprocess
import sys
import tempfile
import shutil
import os

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!")
    
    command = sys.argv[3]
    args = sys.argv[4:]
    
    with tempfile.TemporaryDirectory() as tempDir:
        os.makedirs(os.path.join(tempDir, os.path.dirname(command).strip("/")))
        shutil.copy(command, os.path.join(tempDir, command.strip("/")))
        os.chroot(tempDir)
        os.unshare(os.CLONE_NEWPID)

        completed_process = subprocess.run([command, *args])
        exit(completed_process.returncode)


if __name__ == "__main__":
    main()
