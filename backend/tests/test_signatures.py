# backend/tests/test_signatures.py
"""
Tests for digital signatures.
"""

import pytest
from crypto.signatures import generate_key_pair, sign_data, verify_signature, SignatureError


def test_key_generation():
    """Test RSA key pair generation."""
    private_key, public_key = generate_key_pair(2048)
    
    assert private_key is not None
    assert public_key is not None
    assert "BEGIN PRIVATE KEY" in private_key
    assert "BEGIN PUBLIC KEY" in public_key


def test_sign_verify_data():
    """Test signing and verifying data."""
    private_key, public_key = generate_key_pair(2048)
    
    data = {"amount": 10000, "member_id": "mem-123", "timestamp": "2026-01-15T10:30:00"}
    
    # Sign
    signature = sign_data(data, private_key)
    assert signature is not None
    assert len(signature) > 0
    
    # Verify
    result = verify_signature(data, signature, public_key)
    assert result is True


def test_signature_tamper_detection():
    """Test that tampered signatures are detected."""
    private_key, public_key = generate_key_pair(2048)
    
    data = {"amount": 10000, "member_id": "mem-123"}
    
    # Sign
    signature = sign_data(data, private_key)
    
    # Tamper with data
    data_tampered = {"amount": 20000, "member_id": "mem-123"}
    
    # Verify should fail
    result = verify_signature(data_tampered, signature, public_key)
    assert result is False


def test_sign_transaction_with_user_key():
    """Test signing a complete transaction."""
    private_key, public_key = generate_key_pair(2048)
    
    transaction = {
        "member_id": "mem-123",
        "amount": 10000.00,
        "transaction_type": "CONTRIBUTION",
        "chama_id": "chama-456",
        "timestamp": "2026-01-15T10:30:00"
    }
    
    signed = sign_transaction_with_user_key(transaction, private_key, public_key)
    
    assert 'signature' in signed
    assert 'public_key' in signed
    assert verify_transaction_signature(signed) is True