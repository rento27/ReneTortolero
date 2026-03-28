import os
import logging

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager():
    """
    Retrieves CSD credentials from Google Secret Manager directly into memory.
    If MOCK_SIGNER is set (for testing), returns None.
    """
    if os.environ.get("MOCK_SIGNER"):
        logger.info("MOCK_SIGNER is set. Returning None for signer.")
        return None

    try:
        from google.cloud import secretmanager
        from satcfdi.models import Signer

        client = secretmanager.SecretManagerServiceClient()
        key_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-key/versions/latest"}).payload.data
        cer_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-cer/versions/latest"}).payload.data
        password = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-pass/versions/latest"}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Failed to load signer from secret manager: {e}")
        return None
