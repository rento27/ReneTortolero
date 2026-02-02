from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def load_signer(project_id: str = "notaria4-core"):
    """
    Loads the CSD (Certificate of Digital Seal) from Google Secret Manager.
    Returns a Signer object initialized in memory.
    NEVER writes keys to disk.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()

        # Define secret paths (versions/latest can be used, or specific versions)
        key_name = f"projects/{project_id}/secrets/csd-key/versions/latest"
        cer_name = f"projects/{project_id}/secrets/csd-cer/versions/latest"
        pass_name = f"projects/{project_id}/secrets/csd-pass/versions/latest"

        # Access secrets
        # Note: In a real Cloud Run env, the service account needs 'Secret Manager Secret Accessor' role
        key_response = client.access_secret_version(request={"name": key_name})
        cer_response = client.access_secret_version(request={"name": cer_name})
        pass_response = client.access_secret_version(request={"name": pass_name})

        key_bytes = key_response.payload.data
        cer_bytes = cer_response.payload.data
        password = pass_response.payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

    except Exception as e:
        print(f"Error loading Signer from Secret Manager: {e}")
        # Return None or raise depending on strictness. For now, raising to halt execution if keys fail.
        raise e
