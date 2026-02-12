from google.cloud import secretmanager
from satcfdi.models import Signer
import logging
import os

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager(project_id: str, version_id: str = "latest"):
    """
    Loads the CSD (Certificate and Key) from Google Secret Manager.
    Returns a Signer object.

    This function expects three secrets to be present in the project:
    - csd-key: The private key file (binary)
    - csd-cer: The certificate file (binary)
    - csd-pass: The password for the key (string)
    """
    # Check for mock/dev environment where we might not have credentials
    if os.environ.get("MOCK_SIGNER") == "true":
         logger.warning("Using mock signer (MOCK_SIGNER=true)")
         return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        # Paths to secrets
        key_name = f"projects/{project_id}/secrets/csd-key/versions/{version_id}"
        cer_name = f"projects/{project_id}/secrets/csd-cer/versions/{version_id}"
        pass_name = f"projects/{project_id}/secrets/csd-pass/versions/{version_id}"

        # Access secrets
        # Note: This requires 'Secret Manager Secret Accessor' role
        # We fetch payload.data directly
        key_resp = client.access_secret_version(request={"name": key_name})
        cer_resp = client.access_secret_version(request={"name": cer_name})
        pass_resp = client.access_secret_version(request={"name": pass_name})

        key_bytes = key_resp.payload.data
        cer_bytes = cer_resp.payload.data
        password = pass_resp.payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

    except Exception as e:
        logger.error(f"Failed to load signer from Secret Manager: {e}")
        raise e
