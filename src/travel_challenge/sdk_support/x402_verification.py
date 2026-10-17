"""Instructor-owned EIP-712 verification; no travel configuration or settlement."""

import time

from eth_account import Account
from eth_account.messages import encode_typed_data
from x402 import match_payload_to_requirements
from x402.mechanisms.evm.eip712 import build_typed_data_for_signing
from x402.mechanisms.evm.types import ExactEIP3009Payload


def verify_local_signature(payload, requirements):
    """Return verified EIP-3009 data, or raise; no balance or chain checks occur."""
    if payload.x402_version != 2 or not match_payload_to_requirements(
        2, payload.model_dump(by_alias=True), requirements.model_dump(by_alias=True),
    ):
        raise ValueError("Payment requirements do not match")
    evm_payload = ExactEIP3009Payload.from_dict(payload.payload)
    authorization = evm_payload.authorization
    if authorization.to.lower() != requirements.pay_to.lower() or authorization.value != requirements.amount:
        raise ValueError("Signed recipient or amount does not match")
    valid_after = int(authorization.valid_after)
    valid_before = int(authorization.valid_before)
    current_time = int(time.time())
    if current_time < valid_after or current_time >= valid_before:
        raise ValueError("Signature is not currently valid")
    domain, message_types, _, message = build_typed_data_for_signing(
        authorization, 84532, requirements.asset, "USDC", "2",
    )
    domain_data = {"name": domain.name, "version": domain.version,
                   "chainId": domain.chain_id, "verifyingContract": domain.verifying_contract}
    signable_message = encode_typed_data(
        domain_data=domain_data, message_types=message_types, message_data=message,
    )
    payer_address = Account.recover_message(signable_message, signature=evm_payload.signature)
    if payer_address.lower() != authorization.from_address.lower():
        raise ValueError("Invalid payer signature")
    return evm_payload