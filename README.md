# UCSD Data Planet Dataset Batch Uploader
## Overview
This is a script used to upload your dataset, especially large dataset to UCSD Data Planet. It will automatically compress each subfoler in your dataset to zip or 7z file, and upload them to the specified remote dataset repo. It is also designed to support multi-process uploading, which can significantly speed up the uploading process. However, this function requires support from the server end, which is not available at this moment. 

This script can run on Linux, Windows, and MacOS. 

Temporarily, the 7z compression is only supported on Windows, and you need to download and set up 7z executable file on your computer. More specifically, you need to download the 7z executable file (standalone version) from [here](https://www.7-zip.org/download.html), and add the path of the executable file to your system environment variable. 

Notice that, on Windows, if your single zipped file is larger than 2GB, you need to use 7z compression due to the function limitation of `PowerShell Compress-Archive`, otherwise, you can use zip compression.

Author: Zhongyang Zhang, Tanay Karve