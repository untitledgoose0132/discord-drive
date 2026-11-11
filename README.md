# Usage
Install deps `pip install -f requirements.txt`
Export the environment variables BOT_TOKEN and CHANNEL_ID accordingly before running.

Upload a file `python main.py up path/to/file`
Download a file `python main.py down filename`
List known uploaded files `python main.py list`
Delete a file (also deletes the Discord messages associated with the file) `python main.py delete filename`

# Notes
All files are uploaded into a single "folder" so they must have unique names, uploading a different file with the same name will override the metadata for the previous file.
Each chunk is encrypted with ChaCha20Poly1305 using a random nonce before being sent to Discord.
The secret key is stored at `./encryptkey`, created if nonexistent, keep this file saved and backed up or else data will become irrecoverable when lost.
