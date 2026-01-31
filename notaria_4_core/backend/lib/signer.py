import os
from google.cloud import secretmanager
from satcfdi.models import Signer

def load_signer(project_id="notaria4", test_mode=False):
    """
    Loads the CSD certificate and key from Google Secret Manager.
    If test_mode is True, it returns a mock signer or uses a local test certificate.
    """
    if test_mode:
        # For testing purposes, we can return None or a dummy signer if available.
        # Ideally, use satcfdi's test certificates.
        return None

    client = secretmanager.SecretManagerServiceClient()

    # Names of secrets (assumed convention)
    key_secret_name = f"projects/{project_id}/secrets/csd-key/versions/latest"
    cer_secret_name = f"projects/{project_id}/secrets/csd-cer/versions/latest"
    pass_secret_name = f"projects/{project_id}/secrets/csd-pass/versions/latest"

    try:
        # Access secrets
        key_response = client.access_secret_version(request={"name": key_secret_name})
        key_bytes = key_response.payload.data

        cer_response = client.access_secret_version(request={"name": cer_secret_name})
        cer_bytes = cer_response.payload.data

        pass_response = client.access_secret_version(request={"name": pass_secret_name})
        password = pass_response.payload.data.decode("utf-8")

        return Signer(
            certificate=cer_bytes,
            key=key_bytes,
            password=password
        )
    except Exception as e:
        print(f"Error loading signer from Secret Manager: {e}")
        # In production this should raise an error
        raise e
