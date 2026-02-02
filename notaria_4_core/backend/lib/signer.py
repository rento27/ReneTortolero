from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def load_signer(project_id: str = "notaria4") -> Signer:
    """
    Loads the CSD credentials directly from Google Secret Manager into memory.
    NEVER writes to disk.
    """
    if os.getenv("ENV") == "development":
        # Mock for development if needed, or error out to enforce security
        # return Signer.load(certificate=..., key=..., password=...)
        pass

    client = secretmanager.SecretManagerServiceClient()

    # Define secret names (these should be in env vars ideally)
    key_name = f"projects/{project_id}/secrets/csd-key/versions/latest"
    cer_name = f"projects/{project_id}/secrets/csd-cer/versions/latest"
    pass_name = f"projects/{project_id}/secrets/csd-pass/versions/latest"

    try:
        # Access secrets
        key_response = client.access_secret_version(request={"name": key_name})
        cer_response = client.access_secret_version(request={"name": cer_name})
        pass_response = client.access_secret_version(request={"name": pass_name})

        key_bytes = key_response.payload.data
        cer_bytes = cer_response.payload.data
        password = pass_response.payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

    except Exception as e:
        print(f"Error loading signer from Secret Manager: {e}")
        raise e
