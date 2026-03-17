import os
import logging

logger = logging.getLogger(__name__)

try:
    from google.cloud import secretmanager
    from satcfdi.models import Signer
except ImportError:
    secretmanager = None
    Signer = None

def load_signer_from_secret_manager() -> 'Signer':
    """
    Safely retrieves CSD credentials from Google Secret Manager directly into memory.
    If MOCK_SIGNER env var is set, returns None for testing purposes.
    """
    if os.environ.get('MOCK_SIGNER'):
        logger.info("MOCK_SIGNER env var set, skipping Secret Manager and returning None.")
        return None

    if not secretmanager or not Signer:
        logger.warning("Secret Manager or satcfdi missing, cannot load real signer.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        # Retrieve secrets into memory
        key_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-key/versions/latest"}).payload.data
        cer_bytes = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-cer/versions/latest"}).payload.data
        password = client.access_secret_version(request={"name": "projects/notaria4/secrets/csd-pass/versions/latest"}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Error loading signer from Secret Manager: {e}")
        return None
