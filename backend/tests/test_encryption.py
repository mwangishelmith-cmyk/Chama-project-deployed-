# backend/tests/test_encryption.py
"""
Tests for AES-256-GCM encryption.
"""

import pytest
from crypto.encryption import encrypt_data, decrypt_data, EncryptionError


def test_basic_encryption_decryption(app):
    """Test basic encryption and decryption round trip."""
    with app.app_context():
        plaintext = "Sensitive financial data: KES 100,000"
        chama_id = "test-chama-123"
        
        # Encrypt
        encrypted = encrypt_data(plaintext, chama_id)
        assert 'ciphertext' in encrypted
        assert 'nonce' in encrypted
        assert len(encrypted['ciphertext']) > 0
        assert len(encrypted['nonce']) > 0
        
        # Decrypt
        decrypted = decrypt_data(encrypted, chama_id)
        assert decrypted == plaintext


def test_encrypt_dict_data(app):
    """Test encryption of dictionary data."""
    with app.app_context():
        data = {
            'member_id': 'mem-123',
            'amount': 10000.00,
            'transaction_type': 'CONTRIBUTION'
        }
        chama_id = "test-chama-123"
        
        encrypted = encrypt_data(data, chama_id)
        decrypted = decrypt_data(encrypted, chama_id)
        decrypted_dict = json.loads(decrypted)
        
        assert decrypted_dict['member_id'] == data['member_id']
        assert float(decrypted_dict['amount']) == data['amount']


def test_encryption_tamper_detection(app):
    """Test that tampering with encrypted data is detected."""
    with app.app_context():
        plaintext = "Important data"
        chama_id = "test-chama-123"
        
        encrypted = encrypt_data(plaintext, chama_id)
        
        # Tamper with ciphertext
        encrypted['ciphertext'] = encrypted['ciphertext'][:-1] + 'X'
        
        # Decryption should fail
        with pytest.raises(EncryptionError):
            decrypt_data(encrypted, chama_id)


def test_wrong_key_decryption(app):
    """Test that decryption fails with wrong chama ID."""
    with app.app_context():
        plaintext = "Sensitive data"
        chama_id_1 = "chama-123"
        chama_id_2 = "chama-456"
        
        encrypted = encrypt_data(plaintext, chama_id_1)
        
        # Decrypt with wrong chama ID
        with pytest.raises(EncryptionError):
            decrypt_data(encrypted, chama_id_2)


def test_encrypted_field_descriptor(app):
    """Test the EncryptedField descriptor."""
    with app.app_context():
        from models import MemberProfile
        
        # Create a member with encrypted phone number
        member = MemberProfile(
            user_id="test-user",
            chama_id="test-chama",
            role="Member"
        )
        member._phone_number = encrypt_data("0712345678", "test-chama")
        db.session.add(member)
        db.session.commit()
        
        # Verify encryption
        assert member._phone_number is not None
        assert isinstance(member._phone_number, dict)
        assert 'ciphertext' in member._phone_number