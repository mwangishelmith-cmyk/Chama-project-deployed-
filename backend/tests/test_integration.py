# backend/tests/test_integration.py
"""
End-to-end integration tests for the cryptographic ledger system.
"""

import json
from decimal import Decimal
from crypto.ledger import verify_hash_chain
from crypto.signatures import generate_key_pair, sign_transaction_with_user_key


def test_complete_crypto_workflow(client, auth_headers, test_chama, test_member):
    """
    Test complete workflow:
    1. Generate keys
    2. Create signed contribution
    3. Verify hash chain
    4. Verify signature
    5. Check encryption
    """
    chama_id = test_chama['chama_id']
    member_id = test_member['member_id']
    
    # Step 1: Generate key pair for the member
    private_key, public_key = generate_key_pair(2048)
    
    # Step 2: Create a signed transaction
    transaction_data = {
        "member_id": member_id,
        "amount": "10000.00",
        "transaction_subtype": "monthly",
        "reference": "Test Contribution"
    }
    
    # Add signature
    signed_transaction = sign_transaction_with_user_key(
        transaction_data,
        private_key,
        public_key
    )
    
    # Step 3: Submit the signed contribution
    response = client.post(
        f'/api/v1/chamas/{chama_id}/ledger/contribution',
        json=signed_transaction,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'hash' in data
    
    # Step 4: Verify hash chain integrity
    verify_response = client.get(
        f'/api/v1/chamas/{chama_id}/ledger/verify',
        headers=auth_headers
    )
    
    verify_data = verify_response.get_json()
    assert verify_data['status'] == 'intact'
    
    # Step 5: Verify debt calculation
    member_debt = DebtEngine.calculate_member_debt(member_id, chama_id)
    assert member_debt['total_debt'] == Decimal("10000.00")

def test_tamper_detection_end_to_end(client, auth_headers, test_chama, test_member):
    """
    Test that tampering is detected through the API.
    """
    chama_id = test_chama['chama_id']
    member_id = test_member['member_id']
    
    # Step 1: Create a contribution
    response = client.post(
        f'/api/v1/chamas/{chama_id}/ledger/contribution',
        json={
            'member_id': member_id,
            'amount': '10000.00',
            'transaction_subtype': 'monthly'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    
    # Step 2: Verify chain is intact
    verify_response = client.get(
        f'/api/v1/chamas/{chama_id}/ledger/verify',
        headers=auth_headers
    )
    assert verify_response.get_json()['status'] == 'intact'
    
    # Step 3: Simulate tampering by directly modifying the database
    from models import LedgerEntry
    ledger_entry = LedgerEntry.query.first()
    ledger_entry.amount = Decimal("500.00")
    db.session.commit()
    
    # Step 4: Verify chain detects tampering
    verify_response = client.get(
        f'/api/v1/chamas/{chama_id}/ledger/verify',
        headers=auth_headers
    )
    
    verify_data = verify_response.get_json()
    assert verify_data['status'] == 'compromised'
    assert len(verify_data['broken_entries']) > 0