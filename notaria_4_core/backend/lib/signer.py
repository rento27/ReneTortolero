from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def load_signer_from_secrets(project_id: str, key_secret_id: str, cer_secret_id: str, pass_secret_id: str) -> Signer:
    """
    Loads the CSD (Certificado de Sello Digital) from Google Secret Manager directly into memory.
    This prevents sensitive key files from touching the disk.

    Args:
        project_id: GCP Project ID
        key_secret_id: Name of the secret containing the .key file bytes
        cer_secret_id: Name of the secret containing the .cer file bytes
        pass_secret_id: Name of the secret containing the password string

    Returns:
        satcfdi.models.Signer object ready for signing XMLs
    """
    client = secretmanager.SecretManagerServiceClient()

    def get_secret(secret_id):
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data

    key_bytes = get_secret(key_secret_id)
    cer_bytes = get_secret(cer_secret_id)
    password_bytes = get_secret(pass_secret_id)
    password = password_bytes.decode("utf-8")

    return Signer.load(
        certificate=cer_bytes,
        key=key_bytes,
        password=password
    )
