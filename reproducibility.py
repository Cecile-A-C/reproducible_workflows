import os
import sys
import shutil
import subprocess
import platform
from datetime import datetime

def save_git_commit_to_file(d="."):
    """
    Save git information to a text file, including:
    - Project name
    - Branch name
    - Current commit hash
    - Some other strings like:
        https://github.com/<user>/{project_name}/commit/{commit_hash}
        https://github.com/<user>/{project_name}/commits/{commit_hash}
        (https://stackoverflow.com/questions/12214746/find-a-commit-on-github-given-the-commit-hash)

    Args:
        d (str): Path to the output text file where the commit info will be saved.
    Returns:
        bool: True if the commit was successfully saved, False otherwise.

    chatgpt says: This function should work properly on all three platforms, as long as:
        Git is installed and available in the system PATH
        Python 3 is installed
        The user has permissions to write to the specified file location
    """
    try:
        # Check if current directory is a git repository
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                       check=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        # Get the current commit hash
        result = subprocess.run(["git", "rev-parse", "HEAD"],
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        commit_hash = result.stdout.decode().strip()

        # Get the current branch name
        branch_result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                       check=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

        branch_name = branch_result.stdout.decode().strip()

        # Get project name (repository name)
        project_name = ""
        try:
            # Get the remote URL
            remote_result = subprocess.run(["git", "config", "--get", "remote.origin.url"],
                                           check=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)

            remote_url = remote_result.stdout.decode().strip()

            # Extract project name from URL
            # This handles formats like:
            # https://github.com/username/project.git
            # git@github.com:username/project.git
            if remote_url.endswith('.git'):
                remote_url = remote_url[:-4]

            project_name = os.path.basename(remote_url)
        except:
            # If we can't get the project name, use the directory name
            project_name = os.path.basename(os.path.abspath(os.curdir))

        # Save all information to the specified file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(d,f"git_commit_{timestamp}.txt"), 'w', encoding='utf-8') as f:
            # f.write(f"Datetime: {datetime.now()}\n")
            f.write(f"Project Name: {project_name}\n")
            f.write(f"Branch Name: {branch_name}\n")
            f.write(f"Commit Hash: {commit_hash}\n")
            f.write(f"View single commit: https://github.com/<user>/{project_name}/commit/{commit_hash}\n")
            f.write(f"View log: https://github.com/<user>/{project_name}/commits/{commit_hash}\n")
            f.write("/!\ the files in the directory may have been modified since the last commit!!\n")

        print(f"Git information saved to {os.path.join(d,f'git_commit_{timestamp}.txt')}")
        return True

    except subprocess.CalledProcessError:
        print("Error: Not a git repository or git is not installed.")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def export_conda_environment(d=".", include_builds=False):
    """
    Export the current conda environment to a YAML file.

    Args:
        d (str): Path to the output text file where the conda env info will be saved.
        include_builds (bool, optional): Whether to include build numbers in the export. Default is False.

    Returns:
        str: Path to the created file
    """
    # Determine the right conda command based on platform
    if platform.system() == "Windows":
        # On Windows, we might need to use conda.bat or find conda in a different way
        conda_cmd = "conda.bat" if os.path.exists(os.path.join(sys.prefix, "Scripts", "conda.bat")) else "conda"
    else:
        conda_cmd = "conda"

    # Get current conda environment name
    result = subprocess.run([conda_cmd, 'info', '--envs'],
                            capture_output=True, text=True,
                            shell=True if platform.system() == "Windows" else False)

    if result.returncode != 0:
        print(f"Error running conda command: {result.stderr}")
        return None

    env_info = result.stdout.strip().split('\n')

    current_env = None
    for line in env_info:
        if '*' in line:  # The active environment is marked with an asterisk
            current_env = line.split()[0]
            if current_env == '*':  # In some formats, the asterisk might be separate
                current_env = line.split()[1]
            break

    if not current_env:
        raise RuntimeError("Could not determine current conda environment")

    # Build the export command
    command = ['conda', 'env', 'export', '-n', current_env]
    if not include_builds:
        command.append('--no-builds')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Run the export command and save to file
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True,
                            shell=True if platform.system() == "Windows" else False)

    if result.returncode != 0:
        print(f"Error exporting environment: {result.stderr}")
        return None

    with open(os.path.join(d,f"conda_env_{timestamp}.yml"), 'w', encoding='utf-8') as f:
        f.write(result.stdout)

    print(f"Environment exported to {os.path.join(d,f'conda_env_{current_env}_{timestamp}.yml')}")

def save_files_rootdir(d=".", extensions=[".py"]):
    """
    Save all the files in the root directory that end with certain extensions

    Args:
        d (str): Path where the files will be saved. """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # save python scripts to text files
    files = [s for s in os.listdir(".") if any(s.endswith(ext) for ext in extensions)]
    # plus any other file
    # files = files + []
    for f in files:
        shutil.copy2(f, os.path.join(d, f"{f}_{timestamp}.txt"))


def make_workflow_reproducible(w_d="."):

    ''' make workflow reproducible (or at least try) '''
    # todo test on mac (works for windows+linux)

    r_d = os.path.join(w_d, "reproducibility")
    if os.path.exists(r_d):
        shutil.rmtree(r_d)
    os.mkdir(r_d)

    # save python scripts to text files
    save_files_rootdir(r_d, extensions=[".py"])

    # save git commit to text file
    save_git_commit_to_file(r_d)

    # save conda env to text file
    export_conda_environment(r_d)

if __name__ == "__main__":
    make_workflow_reproducible()