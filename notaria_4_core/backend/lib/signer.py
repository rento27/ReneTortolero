from google.cloud import secretmanager
from satcfdi.models import Signer
import os

def load_signer(project_id: str = "notaria4", version: str = "latest") -> Signer:
    """
    Loads the CSD (Certificate of Digital Seal) from Google Secret Manager.
    Returns a Signer object to be used by satcfdi.
    """
    # Check if we are in a test environment or have local keys override
    if os.getenv("TEST_MODE") == "True":
        try:
            # Load from local files for testing
            # Assuming these files are placed in a known location during test setup
            cert_path = "tests/assets/cert.pem"
            key_path = "tests/assets/key.pem"

            if os.path.exists(cert_path) and os.path.exists(key_path):
                with open(cert_path, "rb") as f:
                    cert_data = f.read()
                with open(key_path, "rb") as f:
                    key_data = f.read()

                return Signer.load(
                    certificate=cert_data,
                    key=key_data,
                    password=b"password" # Dummy password for testing
                )
        except Exception as e:
            print(f"Warning: Could not load test keys: {e}")
            return None

    try:
        client = secretmanager.SecretManagerServiceClient()

        # Construct resource names
        key_name = f"projects/{project_id}/secrets/csd-key/versions/{version}"
        cer_name = f"projects/{project_id}/secrets/csd-cer/versions/{version}"
        pass_name = f"projects/{project_id}/secrets/csd-pass/versions/{version}"

        # Access secrets
        key_payload = client.access_secret_version(request={"name": key_name}).payload.data
        cer_payload = client.access_secret_version(request={"name": cer_name}).payload.data
        password = client.access_secret_version(request={"name": pass_name}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_payload, key=key_payload, password=password)
    except Exception as e:
        # In production, this should log validation errors.
        # For now, if we can't connect (e.g. no creds), we assume it's development without keys.
        print(f"Error loading secrets: {e}")
        return None
