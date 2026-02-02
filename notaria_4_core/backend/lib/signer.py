import os
from satcfdi.models import Signer

class SignerLoader:
    def __init__(self, project_id: str = "notaria4-core"):
        self.project_id = project_id
        self.test_mode = os.getenv("TEST_MODE", "False").lower() == "true"

    def load_signer(self) -> Signer:
        """
        Loads the Signer object with the CSD certificate and private key.
        In TEST_MODE, returns a mock signer.
        In PROD, fetches credentials from Google Secret Manager.
        """
        if self.test_mode:
            return self._load_mock_signer()
        else:
            return self._load_from_secret_manager()

    def _load_mock_signer(self):
        """
        Loads a dummy signer for local testing purposes.
        In a real scenario, we would load the SAT Test CSDs (CSD_Pruebas_CFDI_LAN7008173R5.key/.cer).
        For this environment, we return a mock object that mimics a Signer to allow code execution without real crypto.
        """
        class MockSigner:
            def __init__(self):
                self.rfc = "AAA010101AAA"
                self.certificate_number = "30001000000300023708"
                self.certificate = "MII..."

            def sign(self, data):
                return b"MOCK_SIGNATURE"

            def verification_code(self, data):
                return "MOCK_VERIFICATION"

            def certificate_base64(self):
                return "MOCK_CERTIFICATE_BASE64"

            def sign_sha256(self, data):
                return "MOCK_SIGNATURE_BASE64"

        return MockSigner()

    def _load_from_secret_manager(self) -> Signer:
        """
        Fetches secrets securely from Google Secret Manager.
        NEVER stores them on disk.
        """
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()

            # Helper to access secret payload
            def get_secret(secret_id):
                name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data

            cer_bytes = get_secret("csd-cer")
            key_bytes = get_secret("csd-key")
            password = get_secret("csd-pass").decode("utf-8")

            return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)

        except ImportError:
            # Fallback if google-cloud-secret-manager is not installed (dev env)
            raise RuntimeError("Google Cloud Secret Manager library not installed.")
        except Exception as e:
            raise RuntimeError(f"Failed to load secrets from GSM: {str(e)}")
