"""GCP helper functions."""

import opentaskpy.otflogging
from google.auth.transport.requests import Request
from google.oauth2 import credentials, service_account
from opentaskpy.exceptions import RemoteTransferError


def get_access_token(credentials_: dict) -> credentials:
    """Get an access token for GCP using the provided credentials.

    Args:
        credentials_: The credentials Service Account object to use
    """
    logger = opentaskpy.otflogging.init_logging(__name__, None, None)
    try:
        # Get an Access Token
        auth_creds = None  # Initialising authCreds

        logger.info("Retrieving credentials")
        auth_creds = service_account.Credentials.from_service_account_info(
            credentials_["credentials"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        auth_creds.refresh(Request())  # Refreshing access token

        if not auth_creds.token:  # Handle exception
            logger.error("Error Retrieving credentials.")
            raise RemoteTransferError("Could not acquire token from GCP")
        logger.info("Successfully generated access token")
        return auth_creds.token  # Return the credentials (token).

    except Exception as e:
        logger.error("Error generating access token")
        logger.exception(e)
