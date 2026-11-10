# backend/tests/test_debt_engine.py
"""
Tests for the debt calculation engine.
"""

from decimal import Decimal
from services.debt_engine import DebtEngine


def test_calculate_member_debt_basic(app, test_chama, test_member):
    """Test basic debt calculation."""
    with app.app_context():
        # Create a contribution
        ledger = LedgerEntry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            is_paid=False,
            status="PENDING"
        )
        db.session.add(ledger)
        db.session.commit()
        
        # Calculate debt
        debt_result = DebtEngine.calculate_member_debt(
            test_member['member_id'],
            test_chama['chama_id']
        )
        
        assert debt_result['total_debt'] == Decimal("10000.00")
        assert debt_result['unpaid_contributions'] == Decimal("10000.00")
        assert debt_result['total_fines'] == Decimal("0.00")
        assert debt_result['total_payments'] == Decimal("0.00")


def test_debt_with_fines(app, test_chama, test_member):
    """Test debt calculation with fines."""
    with app.app_context():
        # Create contribution
        ledger = LedgerEntry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            is_paid=False,
            status="PENDING"
        )
        db.session.add(ledger)
        
        # Create fine
        fine = LedgerEntry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="FINE",
            fine_amount=Decimal("500.00"),
            is_paid=False,
            status="UNPAID"
        )
        db.session.add(fine)
        db.session.commit()
        
        # Calculate debt
        debt_result = DebtEngine.calculate_member_debt(
            test_member['member_id'],
            test_chama['chama_id']
        )
        
        assert debt_result['total_debt'] == Decimal("10500.00")
        assert debt_result['total_fines'] == Decimal("500.00")


def test_debt_with_payments(app, test_chama, test_member):
    """Test debt calculation with payments."""
    with app.app_context():
        # Create contribution
        ledger = LedgerEntry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            is_paid=False,
            status="PENDING"
        )
        db.session.add(ledger)
        
        # Create payment
        payment = LedgerEntry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="PAYMENT",
            amount=Decimal("3000.00"),
            is_paid=True,
            status="COMPLETED"
        )
        db.session.add(payment)
        db.session.commit()
        
        # Calculate debt
        debt_result = DebtEngine.calculate_member_debt(
            test_member['member_id'],
            test_chama['chama_id']
        )
        
        assert debt_result['total_debt'] == Decimal("7000.00")
        assert debt_result['total_payments'] == Decimal("3000.00")


def test_payment_allocation(app, test_chama, test_member):
    """Test FIFO payment allocation."""
    with app.app_context():
        # Create two contributions
        entry1 = LedgerEntry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("10000.00"),
            due_date=datetime(2026, 1, 15),
            is_paid=False,
            status="PENDING"
        )
        db.session.add(entry1)
        
        entry2 = LedgerEntry(
            chama_id=test_chama['chama_id'],
            member_id=test_member['member_id'],
            transaction_type="CONTRIBUTION",
            amount=Decimal("5000.00"),
            due_date=datetime(2026, 2, 15),
            is_paid=False,
            status="PENDING"
        )
        db.session.add(entry2)
        db.session.commit()
        
        # Allocate payment
        allocations = DebtEngine.allocate_payment(
            test_member['member_id'],
            test_chama['chama_id'],
            Decimal("12000.00")
        )
        
        # First entry should be fully paid
        assert allocations[0]['allocated_amount'] == Decimal("10000.00")
        assert allocations[0]['remaining_balance'] == Decimal("0.00")
        
        # Second entry should have remaining
        assert allocations[1]['allocated_amount'] == Decimal("2000.00")
        assert allocations[1]['remaining_balance'] == Decimal("3000.00")