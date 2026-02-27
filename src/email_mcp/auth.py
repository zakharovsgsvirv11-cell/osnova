"""Exchange server authentication and connection management."""

import logging
import os

from exchangelib import (
    Account,
    Configuration,
    Credentials,
    DELEGATE,
)

logger = logging.getLogger(__name__)


class AuthError(Exception):
    pass


def create_account() -> Account:
    """Create an authenticated Exchange account from environment variables.

    Required env vars: EXCHANGE_SERVER, EXCHANGE_USERNAME, EXCHANGE_PASSWORD, EXCHANGE_EMAIL.
    Raises AuthError if credentials are missing or connection fails.
    """
    server = os.getenv("EXCHANGE_SERVER", "")
    username = os.getenv("EXCHANGE_USERNAME", "")
    password = os.getenv("EXCHANGE_PASSWORD", "")
    email = os.getenv("EXCHANGE_EMAIL", "")

    if not all([server, username, password, email]):
        raise AuthError(
            "Missing Exchange credentials. "
            "Set EXCHANGE_SERVER, EXCHANGE_USERNAME, EXCHANGE_PASSWORD, EXCHANGE_EMAIL in .env"
        )

    try:
        credentials = Credentials(username=username, password=password)
        config = Configuration(server=server, credentials=credentials)
        account = Account(
            primary_smtp_address=email,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
        # Verify connection by accessing root folder
        _ = account.root
        logger.info("Connected to Exchange server %s as %s", server, email)
        return account
    except Exception as e:
        raise AuthError(f"Failed to connect to Exchange: {e}") from e
