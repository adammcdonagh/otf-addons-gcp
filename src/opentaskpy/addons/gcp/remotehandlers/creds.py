"""GCP helper functions."""

import opentaskpy.otflogging
from opentaskpy.exceptions import RemoteTransferError
from google.oauth2 import service_account
from google.auth.transport.requests import Request


def get_access_token(credentials: dict) -> dict:
    """Get an access token for GCP using the provided credentials.

    Args:
        credentials: The credentials to use
    """
    # Get an Access Token

    logger = opentaskpy.otflogging.init_logging(__name__, None, None)

    credentials = service_account.Credentials.from_service_account_info(
        credentials, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())

    print(credentials)

    if not credentials.token:
        raise RemoteTransferError(
            f"Could not acquire token from GCP"
        )

    return credentials.token            #Return the token.

