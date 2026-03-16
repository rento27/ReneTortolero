import os
import logging
try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager():
    """
    Safely retrieves CSD credentials from Google Secret Manager directly into memory.
    If MOCK_SIGNER env var is set, it returns None to allow testing.
    """
    if os.environ.get("MOCK_SIGNER"):
        logger.info("MOCK_SIGNER is set. Bypassing Secret Manager and returning None.")
        return None

    if not secretmanager or not Signer:
        logger.warning("Secret Manager or satcfdi is not available. Cannot load signer.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "notaria4")

        key_path = f"projects/{project_id}/secrets/csd-key/versions/latest"
        cer_path = f"projects/{project_id}/secrets/csd-cer/versions/latest"
        pass_path = f"projects/{project_id}/secrets/csd-pass/versions/latest"

        key_bytes = client.access_secret_version(request={"name": key_path}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_path}).payload.data
        password = client.access_secret_version(request={"name": pass_path}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Failed to load signer from secret manager: {e}")
        return None
