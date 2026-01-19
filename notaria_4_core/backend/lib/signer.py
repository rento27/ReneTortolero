from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def load_signer(project_id: str, key_version: str = "latest", cer_version: str = "latest", pass_version: str = "latest") -> Signer:
    """
    Loads CSD credentials directly from Google Secret Manager into memory.
    NEVER writes to disk.

    Args:
        project_id: GCP Project ID.
        key_version: Version of the .key secret.
        cer_version: Version of the .cer secret.
        pass_version: Version of the password secret.

    Returns:
        satcfdi.models.Signer object ready for signing.
    """
    client = secretmanager.SecretManagerServiceClient()

    # Helper to fetch bytes
    def get_secret(secret_id: str) -> bytes:
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{key_version}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data

    # Fetch secrets
    # Assumes secret names are standard: csd-key, csd-cer, csd-pass
    try:
        key_bytes = get_secret("csd-key")
        cer_bytes = get_secret("csd-cer")
        password_bytes = get_secret("csd-pass")

        return Signer.load(
            certificate=cer_bytes,
            key=key_bytes,
            password=password_bytes.decode("utf-8")
        )
    except Exception as e:
        # Log error securely (don't log the secrets!)
        print(f"Error loading signer from Secret Manager: {e}")
        raise RuntimeError("Failed to initialize Fiscal Signer")
