import os
import logging
try:
    from satcfdi.models import Signer
    from google.cloud import secretmanager
except ImportError:
    Signer = None
    secretmanager = None

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager():
    """
    Securely retrieves CSD credentials from Google Secret Manager directly into memory.
    If MOCK_SIGNER environment variable is set, defaults to None for testing.
    Raises ValueError if satcfdi or google-cloud-secret-manager are not available.
    """
    if os.environ.get("MOCK_SIGNER"):
        logger.info("MOCK_SIGNER is set. Using mocked signer (None).")
        return None

    if not Signer or not secretmanager:
        logger.error("Missing required libraries for Secret Manager integration.")
        raise ValueError("Missing required libraries for Secret Manager integration.")

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
