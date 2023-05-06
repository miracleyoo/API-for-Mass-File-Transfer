# UCSD Data Planet Dataset Batch Uploader
## Overview
This is a script used to upload your dataset, especially large dataset to UCSD Data Planet. It will automatically compress each subfoler in your dataset to zip or 7z file, and upload them to the specified remote dataset repo. It is also designed to support multi-process uploading, which can significantly speed up the uploading process. However, this function requires support from the server end, which is not available at this moment. 

This script can run on Linux, Windows, and MacOS. 

## Usage

```bash
Upload files to you dataverse.

optional arguments:
  -h, --help            show this help message and exit
  --key KEY             Get this token from your dataverse account. Format:
                        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  --doi DOI             Persistent ID of your dataset. Get this from your
                        dataset metadata. Format: doi:xx.xxxx/xxx/xxxxxx
  -f FILE, --file FILE  File to upload.
  -d DIR, --dir DIR     Directory containing files to upload
  --description DESCRIPTION
                        Brief description of the file(s) to upload.
  --tree TREE           Sub directory structure for tree format for uploaded
                        data.
  -z, --use_7z          Use 7z to zip directories. If not set, the default zip
                        command will be used.
  -n PROCESS_NUM, --process_num PROCESS_NUM
                        Number of processes to use. Default is 1.
  -s, --silent_upload   Do not print upload progress.
  -c {zip,7z}, --compress_type {zip,7z}
                        The compression type to use. Default is zip.
```

By default, we suggest you save your `doi` and `key` in a file named `credential.yaml` in the same directory as the script. The script will automatically parse the content and you don't need to input your credential manually each time. The format of the file is as follows:

```yaml
doi: <YOUR_DATAPLANET_DATASET_DOI>
key: <YOUR_DATAPLANET_KEY>
```


Sample command (Use `7z` on windows):

```bash
python .\data_uploader_mp.py --dir="<YOUR_DATASET_DIR>" --use_7z
```

Sample command (Use `zip` on windows):

```bash
python .\data_uploader_mp.py --dir="<YOUR_DATASET_DIR>"
```

Sample command (Use `zip` on Linux or MacOS):

```bash
python .\data_uploader_mp.py --dir="<YOUR_DATASET_DIR>"
```

Sample command (Not using `credential.yaml`):

```bash
python .\data_uploader_mp.py --dir="<YOUR_DATASET_DIR> --doi="<YOUR_DATAPLANET_DATASET_DOI>" --key="<YOUR_DATAPLANET_API_KEY>"
```


Temporarily, the 7z compression is only supported on Windows, and you need to download and set up 7z executable file on your computer. More specifically, you need to download the 7z executable file (standalone version) from [here](https://www.7-zip.org/download.html), and add the path of the executable file to your system environment variable. 

Notice that, on Windows, if your single zipped file is larger than 2GB, you need to use 7z compression due to the function limitation of `PowerShell Compress-Archive`, otherwise, you can use zip compression.



Author: Zhongyang Zhang, Tanay Karve