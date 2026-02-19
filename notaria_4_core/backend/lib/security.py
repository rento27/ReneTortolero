import os
import logging
from satcfdi.models import Signer
try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager(project_id="notaria4-core", version="latest"):
    """
    Loads the CSD Signer from Google Secret Manager.
    Expects secrets: csd-key, csd-cer, csd-pass.
    """
    if os.environ.get("MOCK_SIGNER"):
        logger.warning("Using MOCK SIGNER as requested by environment.")
        return None

    if not secretmanager:
        logger.error("google-cloud-secret-manager library not installed.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        def access_secret(secret_id):
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data

        # Load secrets
        key_bytes = access_secret("csd-key")
        cer_bytes = access_secret("csd-cer")
        password_bytes = access_secret("csd-pass")
        # Ensure password is correct type (bytes or str depending on library)
        # satcfdi typically accepts bytes or string.
        # Secret Manager returns bytes. Decode to string for password usually.
        password = password_bytes.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

    except Exception as e:
        logger.error(f"Failed to load signer from Secret Manager: {e}")
        # In production, this should probably raise.
        # But if no credentials available (e.g. locally without auth), raise.
        raise e
