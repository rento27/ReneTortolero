from google.cloud import secretmanager
from satcfdi.models import Signer

def load_signer_from_secrets(project_id: str, secret_names: dict) -> Signer:
    """
    Loads the CSD (Certificate, Key, Password) directly from Google Secret Manager into memory.
    NEVER writes to disk.

    secret_names format:
    {
        'key': 'projects/.../secrets/csd-key/versions/latest',
        'cer': 'projects/.../secrets/csd-cer/versions/latest',
        'pass': 'projects/.../secrets/csd-pass/versions/latest'
    }
    """
    client = secretmanager.SecretManagerServiceClient()

    key_bytes = client.access_secret_version(request={"name": secret_names['key']}).payload.data
    cer_bytes = client.access_secret_version(request={"name": secret_names['cer']}).payload.data
    password_bytes = client.access_secret_version(request={"name": secret_names['pass']}).payload.data

    password = password_bytes.decode("utf-8")

    return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
