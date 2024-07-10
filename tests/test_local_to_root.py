# pylint: skip-file
# ruff: noqa
# mypy: ignore-errors
import json
import os
from copy import deepcopy

import pytest
from dotenv import load_dotenv
from opentaskpy.taskhandlers import transfer

# Set the log level to maximum
os.environ["OTF_LOG_LEVEL"] = "DEBUG"


bucket_destination_definition = {
    "bucket": "bucket-test-gcpupload",
    "directory": "",
    "protocol": {
        "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
        "credentials": {},
    },
}


@pytest.fixture(scope="session")
def gcp_creds():
    # If this is not github actions, then load variables from a .env file at the root of
    # the repo
    if "GITHUB_ACTIONS" not in os.environ:
        # Load contents of .env into environment
        # Get the current directory
        current_dir = os.path.dirname(os.path.realpath(__file__))
        load_dotenv(dotenv_path=f"{current_dir}/../.env")

    with open(f"{current_dir}/testFiles/testprojectglue-2fb4b71447c4.json", "r") as f:
        keyR = f.read()

    return json.loads(keyR)


def test_local_to_gcp_transfer(gcp_creds):

    task_definition = {
        "type": "transfer",
        "source": {
            "directory": "src/tmp",
            "fileRegex": ".*\\.txt",
            "protocol": {"name": "local"},
        },
        "destination": [deepcopy(bucket_destination_definition)],
    }
    task_definition["destination"][0]["protocol"]["credentials"] = gcp_creds

    transfer_obj = transfer.Transfer(None, "local-to-gcp-bucket", task_definition)

    assert transfer_obj.run()
