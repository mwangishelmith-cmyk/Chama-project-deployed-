# backend/tests/conftest.py
"""
Pytest configuration and fixtures for cryptographic testing.
"""

import pytest
import json
from datetime import datetime
from decimal import Decimal

from app import create_app
from extensions import db
from models import User, Chama, MemberProfile, ChamaAccount, LedgerEntry, AuditTrail


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['MASTER_ENCRYPTION_KEY'] = 'test-master-key-2024'
    app.config['ENCRYPTION_PEPPER'] = 'test_pepper_2024'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for making requests."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for test requests."""
    # Register and login a test user
    client.post('/api/v1/auth/register', json={
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'full_name': 'Test User'
    })
    
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'TestPassword123!'
    })
    
    token = response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def test_chama(client, auth_headers):
    """Create a test chama for testing."""
    response = client.post('/api/v1/chamas', 
        json={
            'name': 'Test Chama',
            'chama_type': 'savings_investment',
            'creator_role': 'Treasurer'
        },
        headers=auth_headers
    )
    return response.get_json()


@pytest.fixture
def test_member(client, auth_headers, test_chama):
    """Create a test member for testing."""
    chama_id = test_chama['chama_id']
    response = client.post(f'/api/v1/chamas/{chama_id}/members',
        json={
            'email': 'member@example.com',
            'role': 'Member'
        },
        headers=auth_headers
    )
    return response.get_json()