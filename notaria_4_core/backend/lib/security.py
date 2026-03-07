import os
import logging

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager():
    if os.getenv("MOCK_SIGNER") == "1":
        logger.info("MOCK_SIGNER is set. Using a mock Signer.")
        return None

    try:
        from google.cloud import secretmanager
        from satcfdi.models import Signer

        client = secretmanager.SecretManagerServiceClient()

        # Load keys from Secret Manager (assuming specific paths)
        key_name = "projects/notaria4/secrets/csd-key/versions/latest"
        cer_name = "projects/notaria4/secrets/csd-cer/versions/latest"
        pass_name = "projects/notaria4/secrets/csd-pass/versions/latest"

        key_bytes = client.access_secret_version(request={"name": key_name}).payload.data
        cer_bytes = client.access_secret_version(request={"name": cer_name}).payload.data
        password = client.access_secret_version(request={"name": pass_name}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

    except Exception as e:
        logger.error(f"Failed to load signer from Google Secret Manager: {e}")
        return None
