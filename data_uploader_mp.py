import os
import json
import yaml
import shutil
import argparse
import subprocess
import multiprocessing as mp
from pathlib2 import Path
from functools import partial

# Add command line prefix for windows
cmd_prefix = "powershell " if os.name == "nt" else ""


def syscall(cmd):
    cmd = cmd_prefix + cmd
    print(cmd)
    os.system(cmd)

def shell(run_cmd):
    print(run_cmd)
    output = subprocess.run(run_cmd,stdout=subprocess.PIPE,shell=True).stdout.decode()
    return output


data = {
        "description":"My description.",
        "directoryLabel":"data/",
        "categories":["Data"], 
        "restrict":"true", 
        "tabIngest":"false"
}

API_TOKEN="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
FILENAME=''
SERVER_URL="https://dataplanet.ucsd.edu"
PERSISTENT_ID="doi:xx.xxxx/xxx/xxxxxx"

def zipdir(dirname, use_7z=False, compress_type='zip'):
    if os.name != 'nt':
        syscall('zip -qr '+dirname+'.zip '+dirname)
        syscall('zip -q '+dirname+'_.zip '+dirname+'.zip')
        output_zip = dirname+'.zip'
    else:
        if use_7z:
            output_zip = zipdir_7z(dirname, compress_type=compress_type)
        else:
            print('Using PowerShell Compress-Archive, which does not support 7z compression. Using zip instead.')
            syscall('Compress-Archive -DestinationPath '+dirname+'.zip  -Path '+dirname)
            syscall('Compress-Archive -DestinationPath '+dirname+'_.zip -Path '+dirname+'.zip')
            output_zip = dirname+'.zip'
    return output_zip
    

def zipdir_7z(dirname, compress_type='zip'):
    """ Zip a directory using 7z. Please note that 7z must be installed on the system and added to the PATH.
        Download 7z from https://www.7-zip.org/download.html, and choose the standalone console version.
    Args:
        dirname (str): The directory to zip.
    Returns:
        str: The path to the zipped directory.
    """
    if compress_type == 'zip':
        output_zip = dirname.rstrip(os.path.sep) + '.zip'
        zip_command = f'7za a -tzip "{output_zip}" "{dirname}"'
    elif compress_type == '7z':
        output_zip = dirname.rstrip(os.path.sep) + '.7z'
        zip_command = f'7za a -t7z "{output_zip}" "{dirname}"'
    else:
        raise ValueError(f'Unsupported compression type: {compress_type}')

    print(zip_command)

    result = subprocess.run(zip_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"Error zipping directory {dirname}: {result.stderr.decode()}")

    return output_zip

#Compress-Archive -DestinationPath test.zip  -Path test
def upload(api_token,filename,persistent_id, silent_upload=False):

    header = f'X-Dataverse-key:{api_token}'
    json_data = json.dumps(json.dumps(data))
    url = f"{SERVER_URL}/api/datasets/:persistentId/add?persistentId={persistent_id}"

    if silent_upload:
        cmd = f"curl -s --retry-all-errors  -H {header} -X POST -F file=@{filename} -F 'jsonData={json_data}' \"{url}\" "
    else:
        cmd = f"curl --retry-all-errors  -H {header} -X POST -F file=@{filename} -F 'jsonData={json_data}' \"{url}\" "
    print('Command: ' + cmd)
    try:
        result = shell(cmd)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        error = {"status":"error","filename":filename,"message":result}
        # failure_list.append(error)
        return error 

    return json.loads(result)


def process_file(file, done_path, args):
    # global done_path, args
    try:
        if os.path.isdir(file):
            if os.path.exists(file + f'.{args.compress_type}'):
                print(f'{file} is already zipped, uploading...')
            else:
                print(file + " is a directory. Zipping.")
                file = zipdir(file, use_7z=args.use_7z, compress_type=args.compress_type)
                print(f'{file} is zipped. Uploading...')
            is_zipped_dir = True

        else:
            is_zipped_dir = False

        if not os.path.isfile(file):
            print(file + " does not exist. skipping.")
            return

        if file[0] == '.' and file[1] not in {"\\", "/"}:
            print(file + ": hidden file, skipping ")
            return

        result = upload(args.key, file, args.doi, silent_upload=args.silent_upload)
        if result["status"] != "OK":
            print("Failed. ")
            print(result)
        else:
            if args.dir is not None:
                with mp.Lock():
                    with open(done_path, 'a') as df:
                        df.write(Path(file).stem + '\n')
            if is_zipped_dir:
                if os.name != "nt":
                    os.remove(file)
                else:
                    os.system('del ' + file)

    except Exception as e:
        print(f"Error processing {file}: {e}")
        with mp.Lock():
            with open('error_files.txt', 'a') as ef:
                ef.write(file + '\n')
        return


def files_uploader(args):
    global done_path
    done_files = set()

    if args.description is not None:
        data["description"] = args.description

    if args.tree is not None:
        data["directoryLabel"] += args.tree

    if args.dir is not None:
        files = [os.path.join(args.dir, f) for f in  os.listdir(args.dir)]

        # Get stem of dir name
        dir_stem = Path(args.dir).stem

        done_path = f'{dir_stem}_done_files.txt'
        if os.path.isfile(done_path):
            print(f'Loading processed file list from {done_path}')
            with open(done_path, 'r') as df:
                for line in df:
                    done_files.add(line.strip())  
            print(f'In total {len(done_files)} files are already uploaded.')

    if args.file is not None:
        files = [args.file]

    files = [f for f in files if Path(f).stem not in done_files]

    # Create a pool of worker processes
    pool = mp.Pool(min(args.process_num, mp.cpu_count()))

    # Map the function to process files to the pool of worker processes
    # Also, pass the done_path and args
    
    pool.map(partial(process_file, done_path=done_path, args=args), files)

    # Close the pool of worker processes
    pool.close()
    pool.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload files to you dataverse.')
    parser.add_argument(
        '--key',type=str,
        help='Get this token from your dataverse account.\n Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    )

    parser.add_argument(
        '--doi',type=str,
        help='Persistent ID of your dataset. Get this from your dataset metadata. \n Format: doi:xx.xxxx/xxx/xxxxxx',
    )
    parser.add_argument(
        '-f', '--file',type=str,
        help='File to upload.'
    )
    parser.add_argument(
        '-d', '--dir',type=str,
        help='Directory containing files to upload'
    )
    parser.add_argument(
        '--description',type=str,
        help='Brief description of the file(s) to upload.',
    )
    parser.add_argument(
        '--tree',type=str,
        help='Sub directory structure for tree format for uploaded data.',
    )

    # add bool arg for use_7z
    parser.add_argument(
        '-z', '--use_7z', action='store_true',
        help='Use 7z to zip directories. If not set, the default zip command will be used.'
    )

    # add arg for process_num
    parser.add_argument(
        '-n', '--process_num', type=int,
        help='Number of processes to use. Default is 1.',
        default=1
    )

    # add arg for silent_upload
    parser.add_argument(
        '-s', '--silent_upload', action='store_true',
        help='Do not print upload progress.'
    )

    args = parser.parse_args()
    args.compress_type = '7z' if args.use_7z else 'zip'

    # Check whether credential.yaml exists
    if os.path.isfile('credential.yaml'):
        # Load credential.yaml
        with open('credential.yaml', 'r') as f:
            credentials = yaml.safe_load(f)
        
        # Check whether key and doi are set, if not, use the values in credential.yaml
        if args.key is None:
            args.key = credentials['key']
        if args.doi is None:
            args.doi = credentials['doi']

    # Check whether key and doi are set
    assert args.key is not None, "Please set --key or create a credential.yaml file."
    assert args.doi is not None, "Please set --doi or create a credential.yaml file."

    if args.process_num > 1:
        args.silent_upload = True

    if (args.file is None) and (args.dir is None):
        raise Exception("Either --file or --dir should be set.")

    files_uploader(args)