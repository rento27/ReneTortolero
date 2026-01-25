from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def cargar_signer(project_id: str = "notaria4") -> Signer:
    """
    Loads CSD credentials from Google Secret Manager.
    Never stores keys on disk.
    """
    # Allow override for testing
    if os.environ.get("TEST_MODE"):
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        def get_secret(name):
            # In a real deployment, the project ID would be dynamic or strictly set
            path = f"projects/{project_id}/secrets/{name}/versions/latest"
            response = client.access_secret_version(request={"name": path})
            return response.payload.data

        print("Loading CSD from Secret Manager...")
        key_bytes = get_secret("csd-key")
        cer_bytes = get_secret("csd-cer")
        password = get_secret("csd-pass").decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        print(f"Error loading secrets: {e}")
        # In production, we must fail.
        raise e
