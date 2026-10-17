"""Real x402 signing and HTTP headers; simulated weather and settlement only."""

from eth_account import Account
from eth_keys.exceptions import BadSignature
from eth_utils import ValidationError as SignatureValidationError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from x402 import PaymentRequired, PaymentRequirements, SettleResponse, x402Client
from x402.http.utils import (
    decode_payment_required_header, decode_payment_response_header,
    decode_payment_signature_header, encode_payment_required_header,
    encode_payment_response_header, encode_payment_signature_header,
)
from x402.mechanisms.evm.exact.client import ExactEvmScheme
from x402.mechanisms.evm.signers import EthAccountSigner

from travel_challenge.sdk_support.x402_verification import verify_local_signature


app = FastAPI(title="Teaching weather: NO real settlement")
REQUIREMENTS = PaymentRequirements(
    scheme="exact", network="eip155:84532", amount="3000",
    asset="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    pay_to="0x0000000000000000000000000000000000000001",
    max_timeout_seconds=60, extra={"name": "USDC", "version": "2"},
)


def make_payment_client():
    """Teacher setup: disposable unfunded signer; no key entry, RPC or wallet app."""
    signer = EthAccountSigner(Account.create())
    return x402Client().register("eip155:84532", ExactEvmScheme(signer))


@app.get("/weather")
def weather(request: Request, city: str = "Tokyo"):
    required = PaymentRequired(
        x402_version=2, accepts=[REQUIREMENTS],
        resource={"url": str(request.url), "description": "Simulated teaching forecast",
                  "mimeType": "application/json"},
    )
    header = request.headers.get("PAYMENT-SIGNATURE")
    if not header:
        return JSONResponse(
            {"error": "Payment required", "settlement": "SIMULATED_NO_FUNDS_MOVED"},
            status_code=402,
            headers={"PAYMENT-REQUIRED": encode_payment_required_header(required)},
        )
    try:
        payload = decode_payment_signature_header(header)
        evm_payload = verify_local_signature(payload, REQUIREMENTS)
    except (ValueError, TypeError, KeyError, OverflowError, BadSignature, SignatureValidationError):
        return JSONResponse({"error": "Invalid payment signature"}, status_code=403)
    receipt = SettleResponse(
        success=True, network=REQUIREMENTS.network, payer=evm_payload.authorization.from_address,
        transaction="SIMULATED:" + evm_payload.authorization.nonce, amount=REQUIREMENTS.amount,
    )
    return JSONResponse(
        {"city": city, "forecast": "rain", "source": "instructor simulation",
         "settlement": "SIMULATED_NO_FUNDS_MOVED"},
        headers={"PAYMENT-RESPONSE": encode_payment_response_header(receipt)},
    )


def read_requirements(response):
    """W3 task 1: require HTTP 402, decode PAYMENT-REQUIRED with the official SDK.

    Return the official PaymentRequired object. Inspect its resource and accepts:
    exact / eip155:84532 / USDC / 3000 minor units = 0.003 USDC.
    """
    raise NotImplementedError("W3 task 1: inspect and decode an actual HTTP 402")


async def pay_for_weather(http, response):
    """W3 task 2: sign, retry the original URL, inspect the official receipt.

    Use await client.create_payment_payload(required), encode_payment_signature_header,
    and http.get(response.request.url, headers={'PAYMENT-SIGNATURE': ...}).
    Require a successful response and decode PAYMENT-RESPONSE with the official SDK.
    Return (response.json(), official SettleResponse). All settlement is simulated.
    """
    required = read_requirements(response)
    client = make_payment_client()
    raise NotImplementedError("W3 task 2: use the official x402 client and HTTP retry")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8020)