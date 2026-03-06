import os
import logging

logger = logging.getLogger(__name__)

try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

def load_signer_from_secret_manager(project_id: str = "notaria4") -> 'Signer':
    if os.environ.get("MOCK_SIGNER") == "1":
        logger.info("Using MOCK_SIGNER")
        return None

    if not secretmanager:
        logger.error("google-cloud-secret-manager not installed")
        return None

    if not Signer:
        logger.error("satcfdi not installed")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        # In a real environment, project_id might be dynamic
        key_name = f"projects/{project_id}/secrets/csd-key/versions/latest"
        cer_name = f"projects/{project_id}/secrets/csd-cer/versions/latest"
        pass_name = f"projects/{project_id}/secrets/csd-pass/versions/latest"

        key_bytes = client.access_secret_version(request={"name": key_name}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_name}).payload.data
        password = client.access_secret_version(request={"name": pass_name}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Failed to load signer from secret manager: {e}")
        return None
