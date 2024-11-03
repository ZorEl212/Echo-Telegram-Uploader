#!/usr/bin/env python3
import json
from datetime import datetime
from jwcrypto import jwe, jwk
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from models import storage, config

class Auth:
    public_key: str = config.get('PUBLIC_KEY')
    private_key: str = config.get('PRIVATE_KEY')

    @classmethod
    def load_private_key(cls) -> jwk.JWK:
        """Load the private key without password protection."""
        try:
            private_key = serialization.load_pem_private_key(
                cls.private_key.encode(),
                backend=default_backend(), password=None
            )
        except Exception as e:
            print(f"Error loading private key: {e}")
            return None

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return jwk.JWK.from_pem(private_key_pem)

    @classmethod
    def verify_token(cls, token: str) -> dict:
        """Verify and decrypt the provided JWE token."""
        private_key = cls.load_private_key()
        if private_key is None:
            return None

        # Create JWE object and deserialize the token
        jwe_token = jwe.JWE()
        try:
            jwe_token.deserialize(token)
            # Decrypt the JWE token
            jwe_token.decrypt(private_key)
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

        # Get the decrypted message (JSON string)
        decrypted_message = jwe_token.payload.decode('utf-8')
        return json.loads(decrypted_message)

    @classmethod
    def create_token(cls, data: dict, sid: str) -> str:
        """Create a JWE token from the provided data."""
        data_string = json.dumps(data)
        public_key = jwk.JWK.from_pem(cls.public_key.encode())
        
        # Create JWE object
        protected_header = {
            "alg": "RSA-OAEP",
            "enc": "A256GCM",
            "typ": "JWE",
            "exp": datetime.now().timestamp() + 3600 * 24,
            "kid": public_key.thumbprint()
        }

        token = jwe.JWE(
            plaintext=data_string.encode('utf-8'),
            recipient=public_key,
            protected=protected_header
        )

        # Serialize the JWE token
        return token.serialize()

    @classmethod
    def check_server_details(cls, user_id: str, server_id: str) -> dict:
        """Check if the server details match the user ID and server ID."""
        server = storage.get('Server', server_id)
        if (server is None or server.id != server_id or server.userId != user_id):
            return False
        return server.to_dict()
