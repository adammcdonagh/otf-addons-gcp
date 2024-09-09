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
current_dir = os.path.dirname(os.path.realpath(__file__))
load_dotenv(dotenv_path=f"{current_dir}/../.env")

bucket_source_root_definition = {
    "bucket": "bucket-test-gcpupload",
    "directory": "",
    "fileRegex": "^rootdir\\d*.txt$",
    "protocol": {
        "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
        "credentials": {},
    },
}
bucket_source_nested_definition = {
    "bucket": "bucket-test-gcpupload",
    "directory": "",
    "fileRegex": ".*\\.txt",
    "protocol": {
        "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
        "credentials": {},
    },
}
bucket_source_nested_regex_definition = {
    "bucket": "bucket-test-gcpupload",
    "directory": "",
    "fileRegex": ".*\\.txt",
    "protocol": {
        "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
        "credentials": {},
    },
}
bucket_local_definition = {
    "directory": current_dir,
    "protocol": {"name": "local"},
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

    with open(f"{current_dir}/creds.json", "r") as f:
        keyR = f.read()

    return json.loads(keyR)


def test_gcp_root_to_local_transfer(gcp_creds):
    task_definition = {
        "type": "transfer",
        "source": deepcopy(bucket_source_root_definition),
        "destination": [deepcopy(bucket_local_definition)],
    }
    task_definition["source"]["protocol"]["credentials"] = gcp_creds

    transfer_obj = transfer.Transfer(None, "gcp-to-local", task_definition)

    assert transfer_obj.run()


def test_gcp_nested_to_local_transfer(gcp_creds):
    task_definition = {
        "type": "transfer",
        "source": deepcopy(bucket_source_nested_definition),
        "destination": [deepcopy(bucket_local_definition)],
    }
    task_definition["source"]["protocol"]["credentials"] = gcp_creds
    task_definition["source"]["fileWatch"] = {
        "timeout": 20,
        "directory": "localnested",
        "fileRegex": ".*\\.txt",
    }

    transfer_obj = transfer.Transfer(None, "gcp-to-local", task_definition)

    assert transfer_obj.run()


def test_gcp_nested_regex_to_local_transfer(gcp_creds):
    task_definition = {
        "type": "transfer",
        "source": deepcopy(bucket_source_nested_regex_definition),
        "destination": [deepcopy(bucket_local_definition)],
    }
    task_definition["source"]["protocol"]["credentials"] = gcp_creds
    task_definition["source"]["fileWatch"] = {
        "timeout": 20,
    }

    transfer_obj = transfer.Transfer(None, "gcp-to-local", task_definition)

    assert transfer_obj.run()


def test_gcp_root_to_local_transfer(gcp_creds):
    task_definition = {
        "type": "transfer",
        "source": deepcopy(bucket_source_root_definition),
        "destination": [deepcopy(bucket_local_definition)],
    }
    task_definition["source"]["protocol"]["credentials"] = gcp_creds

    transfer_obj = transfer.Transfer(None, "gcp-to-local", task_definition)

    assert transfer_obj.run()


def test_gcp_file_watch(gcp_creds):
    task_definition = {
        "type": "transfer",
        "source": deepcopy(bucket_source_root_definition),
        "destination": [deepcopy(bucket_local_definition)],
    }
    task_definition["source"]["fileWatch"] = {
        "timeout": 20,
        "fileRegex": ".*\\.tx$",
    }
    task_definition["source"]["protocol"]["credentials"] = gcp_creds
    transfer_obj = transfer.Transfer(None, "gcp-to-local", task_definition)

    assert transfer_obj.run()
