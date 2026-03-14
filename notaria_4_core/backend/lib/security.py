import os
import logging

try:
    from satcfdi.models import Signer
except ImportError:
    Signer = None

try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager() -> 'Signer':
    if os.environ.get('MOCK_SIGNER') == '1' or not Signer:
        logger.info("MOCK_SIGNER is enabled or satcfdi is not available. Returning None for signer.")
        return None

    if not secretmanager:
        logger.warning("google-cloud-secret-manager not installed. Cannot load real signer.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'notaria4')

        # Keys and Certs path
        key_name = f"projects/{project_id}/secrets/csd-key/versions/latest"
        cer_name = f"projects/{project_id}/secrets/csd-cer/versions/latest"
        pass_name = f"projects/{project_id}/secrets/csd-pass/versions/latest"

        # Access secrets directly to memory
        key_bytes = client.access_secret_version(request={"name": key_name}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_name}).payload.data
        password = client.access_secret_version(request={"name": pass_name}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Error loading signer from Secret Manager: {e}")
        return None
