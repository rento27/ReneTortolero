import os
import logging
from typing import Optional
from satcfdi.models import Signer

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager() -> Optional[Signer]:
    """
    Safely retrieves CSD credentials from Secret Manager, or returns None if MOCK_SIGNER environment variable is set.
    """
    if os.environ.get('MOCK_SIGNER'):
        logger.info("Mock signer enabled, returning None.")
        return None

    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()

        # In a real environment, project ID would be configured properly.
        # Using placeholder 'notaria4' per the documentation examples.
        key_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-key/versions/latest"}).payload.data
        cer_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-cer/versions/latest"}).payload.data
        password = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-pass/versions/latest"}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Failed to load signer from secret manager: {e}")
        return None
