import os
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)

# Check for satcfdi availability
try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

def load_signer_from_secret_manager():
    """
    Retrieves CSD credentials from Google Secret Manager directly into memory.
    If MOCK_SIGNER env var is set, returns None for testing.
    """
    if os.environ.get("MOCK_SIGNER"):
        logger.info("MOCK_SIGNER is set. Returning None for Signer.")
        return None

    if not Signer:
        logger.error("satcfdi library not found. Cannot load Signer.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        # Ensure project id is retrieved from environment or hardcoded correctly for deployment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "notaria4")

        # Paths for secrets
        key_path = f"projects/{project_id}/secrets/csd-key/versions/latest"
        cer_path = f"projects/{project_id}/secrets/csd-cer/versions/latest"
        pass_path = f"projects/{project_id}/secrets/csd-pass/versions/latest"

        key_bytes = client.access_secret_version(request={"name": key_path}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_path}).payload.data
        password = client.access_secret_version(request={"name": pass_path}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Error loading signer from Secret Manager: {e}")
        return None
