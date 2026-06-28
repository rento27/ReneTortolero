import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

def request_nom151_constancia(document_hash: str) -> dict:
    """
    Mocks an integration with a PSC (e.g., WeeSign, Mifiel) to stamp the PDF hash
    for NOM-151 Constancias de Conservación.

    Args:
        document_hash (str): The SHA-256 hash of the document to stamp.

    Returns:
        dict: A dictionary containing the mock response from the PSC.
    """
    logger.info(f"Requesting NOM-151 Constancia for hash: {document_hash}")

    # Mock PSC response
    return {
        "status": "success",
        "psc": "WeeSign Mock",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "document_hash": document_hash,
        "constancia_id": str(uuid.uuid4()),
        "signature": "MOCKED_NOM151_SIGNATURE_DATA"
    }
