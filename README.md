[![PyPi](https://img.shields.io/pypi/v/otf-addons-gcp.svg)](https://pypi.org/project/otf-addons-gcp/)
![unittest status](https://github.com/adammcdonagh/otf-addons-gcp/actions/workflows/lint.yml/badge.svg)
[![Coverage](https://img.shields.io/codecov/c/github/adammcdonagh/otf-addons-gcp.svg)](https://codecov.io/gh/adammcdonagh/otf-addons-gcp)
[![License](https://img.shields.io/github/license/adammcdonagh/otf-addons-gcp.svg)](https://github.com/adammcdonagh/otf-addons-gcp/blob/master/LICENSE)
[![Issues](https://img.shields.io/github/issues/adammcdonagh/otf-addons-gcp.svg)](https://github.com/adammcdonagh/otf-addons-gcp/issues)
[![Stars](https://img.shields.io/github/stars/adammcdonagh/otf-addons-gcp.svg)](https://github.com/adammcdonagh/otf-addons-gcp/stargazers)

This repository contains addons to allow integration with GCP Cloud Storage via [Open Task Framework (OTF)](https://github.com/adammcdonagh/open-task-framework)

Open Task Framework (OTF) is a Python based framework to make it easy to run predefined file transfers and scripts/commands on remote machines.

This addons allows pushes and pulls of Files from (and to) GCP Cloud Storage Buckets.

# GCP SA Credentials

This package uses `google-auth` to get OAuth2.0 creds for the GCP Token API. This includes `access_token`.

Prior to using this framework, a GCP IAM Service Account should be created through gcloud CLI or Web portal. The JSON credentials for the Service account should be exported and stored locally.
(currently the .gitignore excludes any .json in the tests folder by default)

The Service account crednetials should be included in `tests/testFiles` and require only the following properties:

```
{
    private_key= "-----BEGIN PRIVATE KEY-----\nMIIEv ....",
    client_email= "file.upload@projectName.iam.gserviceaccount.com",
    token_uri= "https://oauth2.googleapis.com/token"
}
```

The rest of the keys can be removed.

Running this OTF Addon, requires test files being placed in the `src/tmp` directory. Running the tests will perform an upload and download from/to GCP Cloud Storage.

Each request will generate a new Service Account Token, token refresh/state-keeping through AWS SSM or local cache has not been implemented yet.

# Transfers

Transfers require a few additional arguments to work. These are:

- bucket: The bucket name of the Cloud Storage instance
- credentials: JSON object containing the above 3 credential properties.

### Supported features

- File transfer: ingress/egress from/to Cloud Storage
  - Renaming functionality
  - PostCopy functionality
  - fileWatch functionality

# Configuration

JSON configs for transfers can be defined as follows:

## Example file upload

```json
"destination": {
    "bucket": "bucketname",
    "directory": "directory/nested",
    "protocol": {
        "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
        "credentials": "{LOOKUP DEFINITION FOR SA CREDENTIALS}",
    },
    "rename":{
        "pattern":"Hithere",
        "sub": "Hi"
    }
}
```

## Example file download

```json
"source": {
    "bucket": "bucketname",
    "directory": "directory/nested",
    "protocol": {
        "name": "opentaskpy.addons.gcp.remotehandlers.bucket.BucketTransfer",
        "credentials": "{LOOKUP DEFINITION FOR SA CREDENTIALS}",
    },
    "postCopyAction":{
        "action":"move",
        "destination": "directory/nested/processed",
        "pattern" : "(?<![^ ])(?=[^ ])(?!ab)",   ## Regex for prefixing
        "sub" : "Archived_"
    },
    "fileRegex": "**.txt" ## Global Expression syntax (only download .txt)
}
```
