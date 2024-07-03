"""GCP Cloud Bucket remote handler."""

import glob
import re
from datetime import datetime

import opentaskpy.otflogging
import requests
from dateutil.tz import tzlocal
from opentaskpy.config.variablecaching import cache_utils
from opentaskpy.exceptions import RemoteTransferError
from opentaskpy.remotehandlers.remotehandler import RemoteTransferHandler

from .creds import get_access_token


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

        self.credentials = get_access_token(self.spec["protocol"])
        print("CREDS OK")
        if "cacheableVariables" in self.spec:
            self.handle_cacheable_variables()

    def handle_cacheable_variables(self) -> None:
        """Handle the cacheable variables."""
        # Obtain the "updated" value from the spec
        for cacheable_variable in self.spec["cacheableVariables"]:
            updated_value = self.obtain_variable_from_spec(
                cacheable_variable["variableName"], self.spec
            )

            cache_utils.update_cache(cacheable_variable, updated_value)

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
        raise NotImplementedError

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

        result = 0
        print("Pulling file")
        if file_list:
            files = list(file_list.keys())
        else:
            files = glob.glob(f"{local_staging_directory}/*")

        for file in files:
            # Strip the directory from the file
            file_name = file.split("/")[-1]
            # Handle any rename that might be specified in the spec
            if "rename" in self.spec:
                rename_regex = self.spec["rename"]["pattern"]
                rename_sub = self.spec["rename"]["sub"]

                file_name = re.sub(rename_regex, rename_sub, file_name)
                self.logger.info(f"Renaming file to {file_name}")

            # Append a directory if one is defined
            if "directory" in self.spec:
                file_name = f"{self.spec['directory']}/{file_name}"

            self.logger.info(
                f"Uploading file: {file} to GCP Bucket {self.spec['bucketName']} with path: {file_name}"
            )

            with open(file, "rb") as file_data:
                response = requests.post(
                    f"https://storage.googleapis.com/upload/storage/v1/b/{self.spec['name']}/o?uploadType=media&name={self.spec['name']}",
                    headers={
                        "Authorization": f"Bearer {self.credentials}",
                        "Content-Type": "application/octet-stream",
                    },
                    data=file_data,
                    timeout=60,
                )

                # Check the response was a success
                if not response.ok:
                    self.logger.error(f"Failed to upload file: {file}")
                    self.logger.error(f"Got return code: {response.status_code}")
                    self.logger.error(response.json())
                    result = 1
                else:
                    self.logger.info(
                        f"Successfully uploaded file to GCP bucket {self.spec['bucketName']}"
                    )

        return result

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
        raise NotImplementedError

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
    ) -> dict:
        return {}

    def tidy(self) -> None:
        """Nothing to tidy."""
