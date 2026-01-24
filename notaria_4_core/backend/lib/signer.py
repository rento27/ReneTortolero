import os
from satcfdi.models import Signer
try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

class CredentialLoader:
    def __init__(self, project_id="notaria4-core"):
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient() if secretmanager else None

    def get_secret(self, secret_id: str, version_id: str = "latest") -> bytes:
        if not self.client:
            # Fallback for local dev/sandbox where GCP auth might be missing
            # In a real scenario, this would raise an error
            print(f"WARNING: Secret Manager client not available. returning mock for {secret_id}")
            return b"MOCK_SECRET"

        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data

    def load_signer(self) -> Signer:
        """
        Loads the CSD certificate and key from Secret Manager and returns a Signer object.
        """
        try:
            # In production, these would be the actual secret names
            cer_content = self.get_secret("csd-cer")
            key_content = self.get_secret("csd-key")
            password = self.get_secret("csd-pass").decode("utf-8")

            return Signer.load(
                certificate=cer_content,
                key=key_content,
                password=password
            )
        except Exception as e:
            print(f"Error loading signer: {e}")
            raise e
