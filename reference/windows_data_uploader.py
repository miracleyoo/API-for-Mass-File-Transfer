import os
import json
import shutil
import argparse
import subprocess
from pathlib2 import Path

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

def zipdir(dirname):
    if os.name != 'nt':
        syscall('zip -qr '+dirname+'.zip '+dirname)
        syscall('zip -q '+dirname+'_.zip '+dirname+'.zip')
        return dirname+'.zip'
    else:
        output_zip = zipdir_7z(dirname)
        # syscall('Compress-Archive -DestinationPath '+dirname+'.zip  -Path '+dirname)
        # syscall('Compress-Archive -DestinationPath '+dirname+'_.zip -Path '+dirname+'.zip')
        return output_zip
    

def zipdir_7z(dirname):
    """ Zip a directory using 7z. Please note that 7z must be installed on the system and added to the PATH.
        Download 7z from https://www.7-zip.org/download.html, and choose the standalone console version.
    Args:
        dirname (str): The directory to zip.
    Returns:
        str: The path to the zipped directory.
    """
    output_zip = dirname.rstrip(os.path.sep) + '.zip'
    zip_command = f'7za a -tzip "{output_zip}" "{dirname}"'

    result = subprocess.run(zip_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"Error zipping directory {dirname}: {result.stderr.decode('utf-8')}")

    return output_zip

#Compress-Archive -DestinationPath test.zip  -Path test
def upload(api_token,filename,persistent_id):

    header = f'X-Dataverse-key:{api_token}'
    json_data = json.dumps(json.dumps(data))
    url = f"{SERVER_URL}/api/datasets/:persistentId/add?persistentId={persistent_id}"

    cmd = f"curl --retry-all-errors  -H {header} -X POST -F file=@{filename} -F 'jsonData={json_data}' \"{url}\" "
    try:
        result = shell(cmd)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        error = {"status":"error","filename":filename,"message":result}
        # failure_list.append(error)
        return error 

    return json.loads(result)

def files_uploader(args):
    api_token = args.key 
    persistend_id = args.doi
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

    for file in files:
        if Path(file).stem in done_files:
            print(f"{file} has already been processed, skipping.")
            continue

        try:
            if os.path.isdir(file):
                if os.path.exists(file+'.zip'):
                    print(f'{file} is already zipped, uploading...')
                    file = file + '.zip'
                else:
                    print(file + " is a directory. Zipping.")
                    file = zipdir(file)
                    print(f'{file} is zipped. Uploading...')
                is_zipped_dir = True

            else:
                is_zipped_dir = False

            if not os.path.isfile(file):
                print(file + " does not exist. skipping.")
                continue

            if file[0] == '.' and file[1] not in {"\\", "/"}:
                print(file + ": hidden file, skipping ")
                continue

            result = upload(api_token, file, persistend_id)
            if result["status"] != "OK":
                print("Failed. ")
                print(result)
            else:
                if args.dir is not None:
                    with open(done_path, 'a') as df:
                        df.write(Path(file).stem + '\n')
                if is_zipped_dir:
                    if os.name != "nt":
                        syscall('rm ' + file)
                        syscall('rm ' + file[:-4] + '.zip')
                    else:
                        syscall('del ' + file)
                        syscall('del ' + file[:-4] + '.zip')

        except Exception as e:
            print(f"Error processing {file}: {e}")
            with open('error_files.txt', 'a') as ef:
                ef.write(file + '\n')
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload files to you dataverse.')
    parser.add_argument(
        '--key',type=str,
        help='Get this token from your dataverse account.\n Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        required=False,
        default='87a80832-fa73-40c4-8e71-2e9183782571',
    )

    parser.add_argument(
        '--doi',type=str,
        help='Persistent ID of your dataset. Get this from your dataset metadata. \n Format: doi:xx.xxxx/xxx/xxxxxx',
        required=False,
        default='doi:10.5072/FK2/STZHOD',
    )
    parser.add_argument(
        '--file',type=str,
        help='File to upload.'
    )
    parser.add_argument(
        '--dir',type=str,
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
    

    args = parser.parse_args()

    if (args.file is None) and (args.dir is None):
        raise Exception("Either --file or --dir should be set.")

    files_uploader(args)