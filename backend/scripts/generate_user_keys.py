# backend/scripts/generate_user_keys.py
"""
Script to generate digital signature keys for a user.
"""

import sys
from app import create_app
from extensions import db
from models import User
from crypto.keys import KeyManager

def generate_keys_for_user(user_email):
    """Generate keys for a specific user."""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"User {user_email} not found")
            return
        
        # Generate keys
        key_manager = KeyManager(user.id, key_scope="user")
        keys = key_manager.get_signature_key_pair()
        
        # Store public key in user record
        user.public_key = keys['public_key']
        db.session.commit()
        
        print(f"✅ Keys generated for {user_email}")
        print(f"Public Key: {keys['public_key'][:100]}...")
        return keys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_user_keys.py <email>")
        sys.exit(1)
    
    generate_keys_for_user(sys.argv[1])