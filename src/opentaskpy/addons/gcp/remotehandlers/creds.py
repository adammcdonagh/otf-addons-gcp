"""GCP helper functions."""

##import opentaskpy.otflogging
from time import time

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from opentaskpy.exceptions import RemoteTransferError


def get_access_token(credentials: dict) -> dict:
    """Get an access token for GCP using the provided credentials.

    Args:
        credentials: The credentials to use
    """
    # Get an Access Token
    authCreds = None  # Initialising authCreds

    # logger = opentaskpy.otflogging.init_logging(__name__, None, None)

    print("Generating Access token from Service account creds")

    authCreds = service_account.Credentials.from_service_account_info(
        credentials["credentialsJson"],
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    authCreds.refresh(Request())  # Refreshing access token

    if not authCreds.token:  # Handle exception
        raise RemoteTransferError(f"Could not acquire token from GCP")

    return credentials  # Return the credentials (token,expiry).
