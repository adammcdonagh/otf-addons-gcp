# pylint: skip-file
# ruff: noqa
# mypy: ignore-errors
import os
from copy import deepcopy

import pytest
from dotenv import load_dotenv
from opentaskpy.taskhandlers import transfer

# Set the log level to maximum
os.environ["OTF_LOG_LEVEL"] = "DEBUG"

local_source_definition = {
    "directory": "./test",
    "filename": "hello.txt",
    "protocol": {"name": "local"}
}

bucket_destination_definition = {
    "bucket": "bucket-test-gcpupload",
    "directory": "helloOTF",
    "protocol": {
        "name": "opentaskpy.addons.gcp.remotehandlers.bucket.Transfer",
        "bucket_credentials_json": {}
    }
}


def test_local_to_sharepoint_transfer():

    task_definition = {
        "type": "transfer",
        "source": deepcopy(local_source_definition),
        "destination": [deepcopy(bucket_destination_definition)],
    }

    transfer_obj = transfer.Transfer(None, "local-to-sharepoint-copy", task_definition)

    assert transfer_obj.run()

