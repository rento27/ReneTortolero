from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def load_signer(project_id: str, key_secret_id: str, cer_secret_id: str, pass_secret_id: str) -> Signer:
    """
    Loads the CSD (Certificate of Digital Seal) from Google Secret Manager.
    CRITICAL: Never writes keys to disk. Loads directly into memory.
    """

    # If in local dev mode without GCP creds, we might need a fallback or mock.
    # For now, we assume the environment is properly configured with a Service Account.

    try:
        client = secretmanager.SecretManagerServiceClient()

        def get_secret(secret_id):
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data

        key_bytes = get_secret(key_secret_id)
        cer_bytes = get_secret(cer_secret_id)
        password_bytes = get_secret(pass_secret_id)

        password = password_bytes.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

    except Exception as e:
        # In a real scenario, we might want to log this securely
        print(f"Error loading signer from Secret Manager: {e}")
        raise e
