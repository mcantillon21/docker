import subprocess
import sys
import tempfile
import shutil
import os
import ctypes

def main():
    
    command = sys.argv[3]
    args = sys.argv[4:]
    
    with tempfile.TemporaryDirectory() as tempDir:
        os.makedirs(os.path.join(tempDir, os.path.dirname(command).strip("/")))
        shutil.copy(command, os.path.join(tempDir, command.strip("/")))
        os.chroot(tempDir)
        
        # Use ctypes to call the unshare() function from the C library with the CLONE_NEWPID flag
        libc = ctypes.CDLL(None)
        CLONE_NEWPID = 0x20000000
        libc.unshare.argtypes = [ctypes.c_int]
        libc.unshare(CLONE_NEWPID)

        completed_process = subprocess.run([command, *args])
        exit(completed_process.returncode)

if __name__ == "__main__":
    main()
