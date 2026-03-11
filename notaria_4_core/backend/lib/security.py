import os
import logging

logger = logging.getLogger(__name__)

try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

def load_signer_from_secret_manager():
    """
    Safely retrieves CSD credentials from Google Secret Manager directly into memory.
    If MOCK_SIGNER env var is set, defaults to None for testing without failing.
    """
    if os.environ.get("MOCK_SIGNER"):
        logger.info("MOCK_SIGNER is set, skipping real Secret Manager retrieval.")
        return None

    try:
        from google.cloud import secretmanager
    except ImportError:
        logger.error("google-cloud-secret-manager not installed. Returning None.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        key_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-key/versions/latest"}).payload.data
        cer_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-cer/versions/latest"}).payload.data
        password = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-pass/versions/latest"}).payload.data.decode("utf-8")

        if Signer:
            return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
        else:
            logger.error("satcfdi Signer not available.")
            return None
    except Exception as e:
        logger.error(f"Failed to load signer from secret manager: {e}")
        return None
