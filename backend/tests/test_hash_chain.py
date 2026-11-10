# backend/tests/test_hash_chain.py
"""
Tests for cryptographic hash chain integrity.
"""

import json
from decimal import Decimal
from crypto.ledger import create_ledger_entry, verify_hash_chain, compute_hash


def test_create_first_ledger_entry(app, test_chama, test_member):
    """Test creating the first ledger entry with hash chain."""
    with app.app_context():
        # Create first ledger entry
        ledger_entry, audit_trail = create_ledger_entry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            transaction_data={
                "subtype": "monthly",
                "reference": "January 2026"
            },
            actor_user_id="test-user-id",
            actor_role="Treasurer"
        )
        
        # Assertions
        assert ledger_entry is not None
        assert audit_trail is not None
        assert audit_trail.previous_hash is None  # First entry has no previous hash
        assert audit_trail.current_hash is not None
        assert len(audit_trail.current_hash) == 64  # SHA-256 is 64 hex chars
        
        # Verify chain integrity
        result = verify_hash_chain(test_chama['chama_id'])
        assert result['status'] == 'intact'
        assert result['verified_count'] == 1
        assert len(result['broken_entries']) == 0

def test_append_to_hash_chain(app, test_chama, test_member):
    """Test appending multiple entries to the hash chain."""
    with app.app_context():
        # Create first entry
        entry1, audit1 = create_ledger_entry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            transaction_data={"subtype": "monthly"},
            actor_user_id="test-user-id",
            actor_role="Treasurer"
        )
        
        # Create second entry
        entry2, audit2 = create_ledger_entry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="PAYMENT",
            amount=Decimal("5000.00"),
            transaction_data={"subtype": "repayment"},
            actor_user_id="test-user-id",
            actor_role="Treasurer"
        )
        
        # Verify chain linking
        assert audit2.previous_hash == audit1.current_hash
        
        # Verify chain integrity
        result = verify_hash_chain(test_chama['chama_id'])
        assert result['status'] == 'intact'
        assert result['verified_count'] == 2

def test_tamper_detection_hash_chain(app, test_chama, test_member):
    """Test that hash chain detects tampering."""
    with app.app_context():
        # Create entries
        entry1, audit1 = create_ledger_entry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            transaction_data={"subtype": "monthly"},
            actor_user_id="test-user-id",
            actor_role="Treasurer"
        )
        
        entry2, audit2 = create_ledger_entry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="PAYMENT",
            amount=Decimal("5000.00"),
            transaction_data={"subtype": "repayment"},
            actor_user_id="test-user-id",
            actor_role="Treasurer"
        )
        
        # Simulate tampering: modify the first entry's data
        audit1.new_data = json.dumps({"tampered": "data"})
        db.session.commit()
        
        # Verify tamper detection
        result = verify_hash_chain(test_chama['chama_id'])
        assert result['status'] == 'compromised'
        assert len(result['broken_entries']) > 0

def test_verify_hash_chain_api(client, auth_headers, test_chama, test_member):
    """Test the API endpoint for hash chain verification."""
    chama_id = test_chama['chama_id']
    
    # Create a ledger entry first
    client.post(f'/api/v1/chamas/{chama_id}/ledger/contribution',
        json={
            'member_id': test_member['member_id'],
            'amount': '10000.00',
            'transaction_subtype': 'monthly'
        },
        headers=auth_headers
    )
    
    # Verify chain integrity
    response = client.get(f'/api/v1/chamas/{chama_id}/ledger/verify',
        headers=auth_headers
    )
    
    data = response.get_json()
    assert data['status'] == 'intact'
    assert data['verified_count'] >= 1
    assert len(data['broken_entries']) == 0

def test_hash_chain_can_append_multiple_entries(app, test_chama, test_member):
    with app.app_context():
        create_ledger_entry(
            chama_id=test_chama["chama_id"],
            member_id=test_member["member_id"],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            transaction_data={
                "subtype": "Monthly",
                "reference": "CONTR-001",
            },
            actor_user_id="test-user-id",
            actor_role="Treasurer",
        )

        create_ledger_entry(
            chama_id=test_chama["chama_id"],
            member_id=test_member["member_id"],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            transaction_data={
                "subtype": "Monthly",
                "reference": "CONTR-002",
            },
            actor_user_id="test-user-id",
            actor_role="Treasurer",
        )

        result = verify_hash_chain(test_chama["chama_id"])

        assert result["status"] == "intact"
        assert result["verified_count"] == 2