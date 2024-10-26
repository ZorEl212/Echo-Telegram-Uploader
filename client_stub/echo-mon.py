import pexpect
import shutil
import signal
import sys
import socket
import json
import configparser
from os import path, getenv
import re
import time
from client_stub.utils import config_loader, config_saver

# Global variables
build_env_sourced = False
child_process = None  # Track the running build process
build_running = False
config = configparser.ConfigParser()
config.add_section('BUILDS')
data_dir = path.join(getenv('HOME'), '.echo')
mock_mode = False  # Test mode flag
ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')  # Matches ANSI escape codes


def signal_handler(sig, frame):
    """Handle SIGINT to stop the build process."""
    global child_process, build_running

    if child_process and child_process.isalive():
        print("\nSending SIGINT to the running process...")
        child_process.sendintr()  # Send interrupt to the child process
        child_process.terminate()  # Ensure the process is terminated
        build_running = False
    else:
        print("\nNo running build process to interrupt.")
    sys.exit(0)  # Exit the script


def source_build_env():
    """Source the build environment if not already sourced."""
    global build_env_sourced, child_process

    if not build_env_sourced:
        print("Sourcing build environment...")
        child_process = pexpect.spawn("/bin/bash", encoding="utf-8", timeout=None)
        child_process.sendline("source build/envsetup.sh")
        child_process.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        child_process.sendline("lunch arrow_ginkgo-userdebug")
        child_process.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        build_env_sourced = True
        print("Build environment sourced successfully.")

def parse_build_line(line):
    """Extract values from a build line using regex after cleaning invalid characters."""
    cleaned_line = ansi_escape.sub('', line)
    
    # Log the cleaned line for debugging
    with open(path.join(data_dir, 'lines.log'), 'a') as log_file:
        log_file.write("Cleaned line: " + cleaned_line + "\n")

    pattern = r"\[\s*(\d+)%\s+(\d+)/(\d+)\]\s+(.+)"  # Regex pattern to fiter metrics
    match = re.search(pattern, cleaned_line)
    
    if match:
        report = {
            'percentage': int(match.group(1)),
            'tasks_done': int(match.group(2)),
            'total_tasks': int(match.group(3)),
            'description': match.group(4)
        }
        
        # Log the result for debugging or verification
        with open(path.join(data_dir, 'lines.log'), 'a') as log_file:
            log_file.write("Parsed report: " + str(report) + "\n")
        
        return report
    else:
        # Log if the line did not match the expected pattern
        with open(path.join(data_dir, 'lines.log'), 'a') as log_file:
            log_file.write("Line did not match pattern: " + cleaned_line + "\n")
        return None


def send_message(socket_path, message):
    """Send a message to the Unix socket or save to JSON if in test mode."""
    if mock_mode:
        save_path = path.join(data_dir, 'mock_output.json')
        with open(save_path, 'a') as mock_file:
            mock_file.write(message + '\n')
        print(f"Mock mode: Message saved to {save_path}")
        return True
    else:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(socket_path)
                client_socket.sendall(message.encode('utf-8'))
                response = client_socket.recv(1024)
                if response:
                    #print("Received response from server:", response.decode('utf-8'))
                    status = json.loads(response.decode('utf-8')).get('success')
                    return response if status else False
                else:
                    return False

        except ConnectionError as e:
            print(f"Connection error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def run_aosp_build():
    """Run the AOSP build process in the foreground."""
    global child_process, build_running

    terminal_size = shutil.get_terminal_size()
    rows, cols = terminal_size.lines, terminal_size.columns

    source_build_env()

    child_process = pexpect.spawn("/bin/bash", encoding="utf-8", timeout=None, maxread=4096) if child_process is None else child_process  # Larger buffer size
    child_process.setwinsize(rows, cols)

    print("Starting the build process...")
    build_running = True

    child_process.logfile_read = sys.stdout  # Let pexpect handle terminal output directly

    child_process.sendline("ota_sign")

    current_line = ""

    while build_running:
        try:
            output = child_process.read_nonblocking(size=4096)
            for char in output:
                if char == '\r': # AOSP build uses carriage return to update the progress on the same line
                    if current_line:
                        with open(path.join(data_dir, 'build_output.log'), 'a') as log_file:
                            log_file.write(current_line + '\n')

                        report = parse_build_line(current_line)
                        if report:
                            message = json.dumps({
                                'progress': report['percentage'],
                                'tasks_done': report['tasks_done'],
                                'total_tasks': report['total_tasks'],
                                'description': report['description']
                            })
                            socket_path = '/tmp/echo.sock'
                            send_message(socket_path, message)
                            time.sleep(0.5)

                        current_line = ""
                else:
                    current_line += char

        except (pexpect.EOF, pexpect.TIMEOUT):
            break

    build_running = False
    print("Build process finished or interrupted.")


def init_build():
    """Simulate build init with mock data in test mode or real data in normal mode."""
    if mock_mode:
        print("In mock mode: Initializing build with mock data...")
        mock_data = {
            'build': {
                'id': 'mock-build-id',
                'dir': path.abspath('.')
            }
        }
        config.set('BUILDS', mock_data.get('build').get('id'), str(mock_data.get('build')))
        config_saver(config, data_dir)
        cached_id_path = path.join(path.abspath('.'), '.build_id')
        with open(cached_id_path, 'w') as f:
            f.write(mock_data.get('build').get('id'))
        save_path = path.join(data_dir, 'mock_build_init.json')
        with open(save_path, 'w') as mock_file:
            json.dump(mock_data, mock_file)
        print(f"Mock mode: Build initialized with mock data and saved to {save_path}")
        return True
    else:
        message = {'command': 'add_build', 'name': sys.argv[2], 'dir': sys.argv[3] if len(sys.argv) > 3 else path.abspath('.')}
        retval = send_message('/tmp/echo.sock', json.dumps(message))
        if retval:
            config.set('BUILDS', retval.get('build').get('id'), retval.get('build'))
            config_saver(config, data_dir)
            cached_id_path = path.join(path.abspath(retval.get('build').get('dir')), '.build_id')
            with open(cached_id_path, 'w') as f:
                f.write(retval.get('build').get('id'))
            return True
        return False


def command_handler():
    """Handle CLI commands."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            print("Initializing build...")
            status = init_build()
            if status:
                print("Build initialized successfully.")
                run_aosp_build()
            else:
                print("Failed to initialize build. Exiting.")
                sys.exit(1)


if __name__ == "__main__":
    if 'test=true' in sys.argv:
        mock_mode = True
        print("Running in test mode. External processes will be mocked.")

    data_dir = path.join(data_dir, 'client3')
    try:
        if path.exists(path.join(data_dir, 'config.bin')):
            print("Loading configuration from secure storage")
            config.read_dict(config_loader(data_dir))
            print(config.items('BUILDS'))
    except Exception as e:
        print(f"Error loading configuration: {e}")

    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) <= 1:
        if path.exists(path.join(path.abspath('.'), '.build_id')):
            print(path.join(path.abspath('.'), '.build_id'))
            with open(path.join(path.abspath('.'), '.build_id'), 'r') as f:
                build_id = f.read()
                if build_id in config['BUILDS']:
                    run_aosp_build()
                else:
                    print("Build ID not found in the configuration. Exiting.")
                    sys.exit(1)
        else:
            print("No build ID found in the current directory. Exiting.")
            sys.exit(1)
    else:
        command_handler()
