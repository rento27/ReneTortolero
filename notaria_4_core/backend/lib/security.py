import os
import logging
from typing import Optional

try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager() -> Optional['Signer']:
    """
    Safely retrieves CSD credentials from Google Secret Manager directly into memory.
    Returns None if retrieval fails or dependencies are missing.
    """
    if not Signer:
        logger.error("Signer is unavailable; returning None.")
        return None

    if not secretmanager:
        logger.error("google-cloud-secret-manager library not found.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        # In a real environment, project ID would be configured properly.
        # Here we use placeholders as defined in the technical requirement documentation.
        key_secret_name = "projects/notaria4/secrets/csd-key/versions/latest"
        cer_secret_name = "projects/notaria4/secrets/csd-cer/versions/latest"
        pass_secret_name = "projects/notaria4/secrets/csd-pass/versions/latest"

        key_bytes = client.access_secret_version(request={"name": key_secret_name}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_secret_name}).payload.data
        password = client.access_secret_version(request={"name": pass_secret_name}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Failed to load signer from secret manager: {e}")
        return None
