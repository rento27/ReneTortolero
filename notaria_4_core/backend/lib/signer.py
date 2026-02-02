from google.cloud import secretmanager
from satcfdi.models import Signer

class SecureSigner:
    def __init__(self, project_id: str, secret_names: dict):
        """
        secret_names dict should contain keys: 'key', 'cer', 'pass'
        mapping to their Secret Manager resource names.
        """
        self.client = secretmanager.SecretManagerServiceClient()
        self.secrets = secret_names

    def load_signer(self) -> Signer:
        """
        Fetches credentials from Secret Manager and loads Signer into memory.
        """
        # Fetch Key
        key_payload = self.client.access_secret_version(
            request={"name": self.secrets['key']}
        ).payload.data

        # Fetch Certificate
        cer_payload = self.client.access_secret_version(
            request={"name": self.secrets['cer']}
        ).payload.data

        # Fetch Password
        pass_payload = self.client.access_secret_version(
            request={"name": self.secrets['pass']}
        ).payload.data.decode("utf-8")

        return Signer.load(
            certificate=cer_payload,
            key=key_payload,
            password=pass_payload
        )
