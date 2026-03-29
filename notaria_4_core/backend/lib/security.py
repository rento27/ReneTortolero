import os
import logging

try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager() -> 'Signer':
    if os.environ.get("MOCK_SIGNER"):
        logger.warning("MOCK_SIGNER is set. Returning None for signer.")
        return None

    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()

        # In a real environment, project ID would be configured
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "notaria4")

        key_name = f"projects/{project_id}/secrets/csd-key/versions/latest"
        cer_name = f"projects/{project_id}/secrets/csd-cer/versions/latest"
        pass_name = f"projects/{project_id}/secrets/csd-pass/versions/latest"

        key_bytes = client.access_secret_version(request={"name": key_name}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_name}).payload.data
        password = client.access_secret_version(request={"name": pass_name}).payload.data.decode("utf-8")

        if Signer:
            return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
        else:
            logger.error("satcfdi library not found, cannot load Signer")
            return None
    except Exception as e:
        logger.error(f"Failed to load signer from Secret Manager: {e}")
        return None
