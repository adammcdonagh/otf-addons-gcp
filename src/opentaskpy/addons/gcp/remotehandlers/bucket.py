"""GCP Cloud Bucket remote handler."""

import glob
import re

import opentaskpy.otflogging
import requests
from opentaskpy.exceptions import RemoteTransferError
from opentaskpy.remotehandlers.remotehandler import RemoteTransferHandler

from .creds import get_access_token

MAX_OBJECTS_PER_QUERY = 100


class BucketTransfer(RemoteTransferHandler):
    """GCP CloudBucket remote transfer handler."""

    TASK_TYPE = "T"

    def __init__(self, spec: dict):
        """Initialise the CloudBucket handler.

        Args:
            spec (dict): The spec for the transfer. This is either the source, or the
            destination spec.
        """
        self.logger = opentaskpy.otflogging.init_logging(
            __name__, spec["task_id"], self.TASK_TYPE
        )
        super().__init__(spec)

        # Generating Access Token for Transfer
        self.credentials = get_access_token(self.spec["protocol"])

    def supports_direct_transfer(self) -> bool:
        """Return False, as all files should go via the worker."""
        return False

    def handle_post_copy_action(self, files: list[str]) -> int:
        """Handle the post copy action specified in the config.

        Args:
            files (list[str]): A list of files that need to be handled.

        Returns:
            int: 0 if successful, 1 if not.
        """
        if "postCopyAction" in self.spec and (
            self.spec["postCopyAction"]["action"] == "move"
            or self.spec["postCopyAction"]["action"] == "rename"
        ):
            try:
                # Append a directory if one is defined

                for file in files:
                    source_file_encoded = file.replace("/", "%2F")
                    dest_file_encoded = f"{self.spec['postCopyAction']['destination'].replace('/','%2F')}%2F{file.split('/')[-1]}"

                    # Check if operation contains renaming
                    if self.spec["postCopyAction"]["action"] == "rename":
                        rename_regex = self.spec["postCopyAction"]["pattern"]
                        rename_sub = self.spec["postCopyAction"]["sub"]
                        dest_file_encoded = re.sub(
                            rename_regex, rename_sub, dest_file_encoded
                        )

                    response = requests.post(
                        f"https://storage.googleapis.com/storage/v1/b/{self.spec['bucket']}/o/{source_file_encoded}/rewriteTo/b/{self.spec['bucket']}/o/{dest_file_encoded}",
                        headers={"Authorization": f"Bearer {self.credentials}"},
                        timeout=1800,
                    )
                    self.logger.info(response.status_code)
                    check_copy = requests.get(
                        f"https://storage.googleapis.com/storage/v1/b/{self.spec['bucket']}/o/{dest_file_encoded}",
                        headers={"Authorization": f"Bearer {self.credentials}"},
                        timeout=1800,
                    )
                    ## Verify file has been copied successfully.
                    if not check_copy.ok:
                        self.logger.info(
                            f"File {dest_file_encoded.replace('%2F','/')} failed to be created in bucket {self.spec['bucket']}"
                        )
                        self.logger.error(check_copy)
                        return 1

                    response = requests.delete(
                        f"https://storage.googleapis.com/storage/v1/b/{self.spec['bucket']}/o/{source_file_encoded}",
                        headers={"Authorization": f"Bearer {self.credentials}"},
                        timeout=1800,
                    )
                    ## Verify file has been deleted successfully.
                    check_delete = requests.get(
                        f"https://storage.googleapis.com/storage/v1/b/{self.spec['bucket']}/o/{source_file_encoded}",
                        headers={"Authorization": f"Bearer {self.credentials}"},
                        timeout=1800,
                    )
                    if check_delete.status_code != 404:
                        self.logger.info(
                            f"File {file} failed to be delete in bucket {self.spec['bucket']}"
                        )
                        self.logger.error(check_delete)
                        return 1

                    self.logger.info(response.status_code)
                    self.logger.info(
                        f"Moved file {file} to {dest_file_encoded.replace('%2F','/')}"
                    )
                return 0
            except Exception as e:
                self.logger.info(
                    f"Error during file copy from {file} to {dest_file_encoded.replace('%2F','/')}"
                )
                self.logger.error(e)
                return 1
        return 1

    def move_files_to_final_location(self, files: list[str]) -> None:
        """Not implemented for this handler."""
        raise NotImplementedError

    # When GCP is the source
    def pull_files(self, files: list[str]) -> None:
        """Not implemented for this handler."""
        raise NotImplementedError

    def push_files_from_worker(
        self, local_staging_directory: str, file_list: dict | None = None
    ) -> int:
        """Push files from the worker to the destination GCP bucket.

        Args:
            local_staging_directory (str): The local staging directory to upload the
            files from.
            file_list (dict, optional): The list of files to transfer. Defaults to None.

        Returns:
            int: 0 if successful, 1 if not.
        """
        try:
            if file_list:
                files = list(file_list.keys())
            else:
                files = glob.glob(f"{local_staging_directory}/*")

            for file in files:
                result = 0
                # Strip the directory from the file
                file_name = file.split("/")[-1]
                # Handle any rename that might be specified in the spec
                if "rename" in self.spec:
                    rename_regex = self.spec["rename"]["pattern"]
                    rename_sub = self.spec["rename"]["sub"]

                    file_name = re.sub(rename_regex, rename_sub, file_name)
                    self.logger.info(f"Renaming file to {file_name}")

                # Append a directory if one is defined
                if "directory" in self.spec and self.spec["directory"] != "":
                    file_name = f"{self.spec['directory']}/{file_name}"

                self.logger.info(
                    f"Uploading file to GCP Bucket {self.spec['bucket']} with path: {file_name}"
                )
                with open(file, "rb") as file_data:
                    response = requests.post(
                        f"https://storage.googleapis.com/upload/storage/v1/b/{self.spec['bucket']}/o",
                        headers={"Authorization": f"Bearer {self.credentials}"},
                        data=file_data,
                        timeout=1800,
                        params={"name": file_name, "uploadType": "media"},
                    )
                    if response.status_code == 401:
                        self.logger.error(f"Unauthorised to Push file: {file}")
                        result = 1
                    elif response.status_code == 403:
                        self.logger.error(f"Failed to Push file: {file}")
                        self.logger.error(
                            f"File already exists or no Delete permissions (for upsert) on Bucket. Status Code: {response.status_code}"
                        )
                        result = 1
                    elif not response.ok:
                        self.logger.error(f"Failed to Push file: {file}")
                        self.logger.error(f"Got return code: {response.status_code}")
                        self.logger.error(response.json())
                        result = 1
                    else:
                        self.logger.info(
                            f"Successfully uploaded {file_name} to GCP bucket {self.spec['bucket']}"
                        )
            return result
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(f"Failed to download file: {file}")
            self.logger.exception(e)
            return 1

    def pull_files_to_worker(
        self, files: list[str], local_staging_directory: str
    ) -> int:
        """Pull files to the worker.

        Download files from GCP to the local staging directory.

        Args:
            files (list): A list of files to download.
            local_staging_directory (str): The local staging directory to download the
            files to.

        Returns:
            int: 0 if successful, 1 if not.
        """
        result = 0
        self.logger.info("Downloading file from GCP.")
        try:
            for file in files:
                self.logger.info(file)
                file = file.replace(
                    "/", "%2F"
                )  # Encoding front slashes from eventual directory

                response = requests.get(
                    f"https://storage.googleapis.com/download/storage/v1/b/{self.spec['bucket']}/o/{file}",
                    headers={"Authorization": f"Bearer {self.credentials}"},
                    timeout=1800,
                    params={"alt": "media"},  # Remove to only grab obj metadata
                )
                if response.status_code == 401:
                    self.logger.error(f"Unauthorized to GET file: {file}")
                    result = 1
                elif response.status_code == 403:
                    self.logger.error(f"Failed to GET file: {file}")
                    self.logger.error(f"Forbidden Status Code: {response.status_code}")
                    result = 1
                elif not response.ok:
                    self.logger.error(f"Failed to GET file: {file}")
                    self.logger.error(f"Got return code: {response.status_code}")
                    self.logger.error(response)
                    result = 1
                else:
                    with open(
                        f"{local_staging_directory}/{file.split('%2F')[-1]}", "wb"
                    ) as f:
                        f.write(response.content)
                    self.logger.info(
                        f"Successfully downloaded {file} to local Staging directory"
                    )
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(f"Failed to download file: {file}")
            self.logger.exception(e)
            result = 1

        return result

    def transfer_files(
        self,
        files: list[str],
        remote_spec: dict,
        dest_remote_handler: RemoteTransferHandler,
    ) -> int:
        """Not implemented for this transfer type."""
        raise NotImplementedError

    def create_flag_files(self) -> int:
        """Not implemented for this transfer type."""
        raise NotImplementedError

    def list_files(
        self, directory: str | None = None, file_pattern: str | None = None
    ) -> list:
        """List Files in GCP with pagination and local regex matching.

        Args:
            directory (str): A directory to list on the bucket.
            file_pattern (str): File pattern to match files.

        Returns:
            list: A list of filenames if successful, an empty list if not.
        """
        self.logger.info("Listing Files in Bucket.")
        try:
            directory = directory or self.spec.get("directory", "")

            base_url = (
                f"https://storage.googleapis.com/storage/v1/b/{self.spec['bucket']}/o"
            )
            headers = {"Authorization": f"Bearer {self.credentials}"}
            params = (
                {"prefix": directory, "maxResults": MAX_OBJECTS_PER_QUERY}
                if directory
                else {}
            )
            items = []

            while True:
                response = requests.get(
                    base_url, headers=headers, params=params, timeout=1800
                )
                if response.status_code == 200:
                    data = response.json()
                    if "items" in data:
                        items.extend(data["items"])

                    if "nextPageToken" in data:
                        # Set the nextPageToken for the next request
                        params["pageToken"] = data["nextPageToken"]
                    else:
                        break
                else:
                    self.logger.error(f"List files returned {response.status_code}")
                    raise RemoteTransferError(response)

            filenames = [
                item["name"]
                for item in items
                if "name" in item
                and (not file_pattern or re.match(file_pattern, item["name"]))
            ]
            return filenames

        except Exception as e:
            self.logger.error(
                f"Error listing files in directory {self.spec['bucket']}/{directory}"
            )
            self.logger.exception(e)
            return []

    def tidy(self) -> None:
        """Nothing to tidy."""
