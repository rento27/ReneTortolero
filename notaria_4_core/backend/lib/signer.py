from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def cargar_signer(project_id="notaria4", secret_key_ver="latest", secret_cer_ver="latest", secret_pass_ver="latest"):
    """
    Loads CSD credentials from Google Secret Manager directly into memory.
    Never writes to disk.
    """
    # If running locally or without GCP credentials, this will fail or need mocks.
    # We allow overrides via env vars for dev.
    if os.environ.get("DEV_MODE") == "true":
        # Return a dummy or None for dev if secrets aren't available
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        # Helper to get secret payload
        def get_secret(name):
            full_name = f"projects/{project_id}/secrets/{name}/versions/{secret_key_ver}"
            response = client.access_secret_version(request={"name": full_name})
            return response.payload.data

        key_bytes = get_secret("csd-key")
        cer_bytes = get_secret("csd-cer")
        password = get_secret("csd-pass").decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        # Log error
        print(f"Error loading secrets: {e}")
        return None
