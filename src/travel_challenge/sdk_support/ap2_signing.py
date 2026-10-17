"""Instructor-owned official AP2 JWT helpers and a local ephemeral merchant key."""

import base64
import hashlib

from ap2.sdk.jwt_helper import create_jwt, verify_jwt
from jwcrypto.common import JWException
from jwcrypto.jwk import JWK


_MERCHANT_KEY = JWK.generate(kty="EC", crv="P-256")


def checkout_hash(token):
    digest = hashlib.sha256(token.encode()).digest()
    encoded_hash = base64.urlsafe_b64encode(digest).decode()
    return encoded_hash.rstrip("=")


def signed_checkout(purchase):
    """Return the SDK-signed local checkout JWT and its hash."""
    token = create_jwt({"alg": "ES256", "typ": "JWT"}, {"purchase": purchase}, _MERCHANT_KEY)
    return token, checkout_hash(token)


def verified_checkout(checkout):
    """Return the signed purchase or raise ValueError; not a full AP2 trust chain."""
    if checkout_hash(checkout.checkout_jwt) != checkout.checkout_hash:
        raise ValueError("Checkout hash does not match its JWT")
    try:
        return verify_jwt(checkout.checkout_jwt, _MERCHANT_KEY)["purchase"]
    except JWException as error:
        raise ValueError("Invalid local merchant checkout signature") from error