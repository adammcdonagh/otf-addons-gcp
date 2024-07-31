# pylint: skip-file
# mypy: allow-untyped-defs
import pytest
from opentaskpy.config.schemas import validate_transfer_json


@pytest.fixture(scope="function")
def valid_local_definition():
    return {"directory": "src", "fileRegex": "", "protocol": {"name": "local"}}


@pytest.fixture(scope="function")
def valid_bucket_destination_definition():
    return [
        {
            "bucket": "bucket-name",
            "directory": "",
            "protocol": {
                "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
                "credentials": {
                    "private_key": "xxx",
                    "token_uri": "https://abc123.com",
                },
            },
        }
    ]


@pytest.fixture(scope="function")
def valid_bucket_source_definition():
    return {
        "bucket": "bucket-name",
        "directory": "directory",
        "fileRegex": "**.txt",
        "protocol": {
            "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
            "credentials": {
                "private_key": "xxx",
                "token_uri": "https://abc123.com",
            },
        },
    }


def test_local_source_no_protocol(valid_local_definition):
    json_data = {
        "type": "transfer",
        "source": valid_local_definition,
        "destination": [{}],
    }
    # Remove protocol
    del json_data["source"]["protocol"]
    assert not validate_transfer_json(json_data)


def test_local_to_gcp_no_credentials(valid_local_definition):
    json_data = {
        "type": "transfer",
        "source": valid_local_definition,
        "destination": [
            {
                "bucket": "bucket-test-gcpupload",
                "directory": "localnested",
                "protocol": {
                    "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
                    "credentials": {},
                },
            }
        ],
    }
    assert not validate_transfer_json(json_data)


def test_local_to_gcp_missing_privKey(
    valid_local_definition, valid_bucket_destination_definition
):
    json_data = {
        "type": "transfer",
        "source": valid_local_definition,
        "destination": valid_bucket_destination_definition,
    }
    del json_data["destination"][0]["protocol"]["credentials"]["private_key"]
    assert not validate_transfer_json(json_data)


def test_local_to_gcp_missing_tokenUri(
    valid_local_definition, valid_bucket_destination_definition
):
    json_data = {
        "type": "transfer",
        "source": valid_local_definition,
        "destination": valid_bucket_destination_definition,
    }
    del json_data["destination"][0]["protocol"]["credentials"]["token_uri"]
    assert not validate_transfer_json(json_data)


def test_local_to_gcp_positive_scenario(
    valid_local_definition, valid_bucket_destination_definition
):
    json_data = {
        "type": "transfer",
        "source": valid_local_definition,
        "destination": valid_bucket_destination_definition,
    }
    assert validate_transfer_json(json_data)


def test_gcp_to_local_missing_bucket(
    valid_local_definition, valid_bucket_source_definition
):
    json_data = {
        "type": "transfer",
        "source": valid_bucket_source_definition,
        "destination": valid_local_definition,
    }
    del json_data["source"]["bucket"]
    assert not validate_transfer_json(json_data)


def test_gcp_to_local_missing_Regex(
    valid_local_definition,
    valid_bucket_source_definition,
):
    json_data = {
        "type": "transfer",
        "source": valid_bucket_source_definition,
        "destination": [valid_local_definition],
    }
    del json_data["source"]["fileRegex"]
    assert not validate_transfer_json(json_data)


def test_gcp_to_gcp(
    valid_bucket_destination_definition, valid_bucket_source_definition
):
    json_data = {
        "type": "transfer",
        "source": valid_bucket_source_definition,
        "destination": valid_bucket_destination_definition,
    }
    assert validate_transfer_json(json_data)


def test_gcp_source_file_watch(valid_bucket_source_definition):
    json_data = {
        "type": "transfer",
        "source": valid_bucket_source_definition,
    }

    json_data["source"]["fileWatch"] = {
        "timeout": 10,
        "directory": "src",
        "fileRegex": ".*\\.txt",
    }

    assert validate_transfer_json(json_data)

    # Remove fileRegex
    del json_data["source"]["fileWatch"]["fileRegex"]
    assert validate_transfer_json(json_data)

    # Remove directory
    del json_data["source"]["fileWatch"]["directory"]
    assert validate_transfer_json(json_data)

    # Add watchOnly
    json_data["source"]["fileWatch"]["watchOnly"] = True
    assert validate_transfer_json(json_data)

    # Add error
    json_data["source"]["error"] = True
    assert validate_transfer_json(json_data)
