import os
import logging
from google.cloud import secretmanager

# We try to import Signer, but it might not be available if satcfdi isn't installed.
try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager():
    """
    Loads the CSD certificate and private key from Google Secret Manager.
    Returns a satcfdi.models.Signer object.
    If MOCK_SIGNER env var is set, it returns None for testing purposes.
    """
    if os.environ.get("MOCK_SIGNER"):
        logger.info("MOCK_SIGNER is set. Returning None for signer.")
        return None

    if Signer is None:
        logger.error("satcfdi library is not available. Cannot create Signer.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        # In a real environment, project ID would be configured properly.
        # Hardcoding the secret paths for Notaria 4 context as seen in the prompt.
        key_secret_name = "projects/notaria4/secrets/csd-key/versions/latest"
        cer_secret_name = "projects/notaria4/secrets/csd-cer/versions/latest"
        pass_secret_name = "projects/notaria4/secrets/csd-pass/versions/latest"

        # Note: Depending on GCP environment configuration, access might fail if
        # credentials are not available.
        key_bytes = client.access_secret_version(request={"name": key_secret_name}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_secret_name}).payload.data
        password = client.access_secret_version(request={"name": pass_secret_name}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Failed to load signer from secret manager: {e}")
        return None
