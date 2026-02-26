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
    Loads the CSD (Certificate, Key, Password) from Google Secret Manager.
    Returns a satcfdi.models.Signer instance.
    """
    # For testing environments without GCP credentials
    if os.environ.get("MOCK_SIGNER"):
        logger.warning("Mocking Signer as per MOCK_SIGNER env var")
        return None

    if not secretmanager or not Signer:
        logger.error("Missing dependencies: google-cloud-secret-manager or satcfdi")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT", "notaria4-prod")

        # Helper to get secret payload
        def get_secret(secret_name):
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data

        # Load secrets
        # Using specific secret names as per prompt or standard convention
        cer_bytes = get_secret("csd-cer")
        key_bytes = get_secret("csd-key")
        password = get_secret("csd-pass").decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

    except Exception as e:
        logger.error(f"Failed to load signer from Secret Manager: {e}")
        return None
