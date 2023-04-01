import subprocess
import sys


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!")
    
    command = sys.argv[3]
    args = sys.argv[4:]
    
    completed_process = subprocess.run([command, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stdout = completed_process.stdout.decode("utf-8").strip() # Remove extra newline character
    stderr = completed_process.stderr.decode("utf-8").strip() # Remove extra newline character
    print(stdout)
    print(stderr, file=sys.stderr)
    
    # completed_process = subprocess.run([command, *args], capture_output=True)
    # print(completed_process.stdout.decode("utf-8"))


if __name__ == "__main__":
    main()
