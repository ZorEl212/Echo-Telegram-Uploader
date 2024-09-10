#!/usr/bin/env python3
import json
from jwcrypto import jwe, jwk
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from models import storage, config
from datetime import datetime

class Auth:

    public_key = config.get('PUBLIC_KEY')
    private_key = config.get('PRIVATE_KEY')
    key_password = config.get('KEY_PASSWORD')

    @classmethod
    def load_private_key_with_password(cls):
        # Load the private key with password protection
        private_key = serialization.load_pem_private_key(
            cls.private_key.encode(),
            password=cls.key_password.encode(),
            backend=default_backend()
        )

        # Convert to jwcrypto format
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        return jwk.JWK.from_pem(private_key_pem)

    @classmethod
    def verify_token(cls, token):
        # Load the private key
        private_key = cls.load_private_key_with_password()

        # Create JWE object and deserialize the token
        jwe_token = jwe.JWE()
        jwe_token.deserialize(token)

        # Decrypt the JWE token
        try:
            jwe_token.decrypt(private_key)
        except Exception as e:
            return None

        # Get the decrypted message (JSON string)
        decrypted_message = jwe_token.payload.decode('utf-8')
        return json.loads(decrypted_message)

    @classmethod
    def create_token(cls, data, sid):
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
        jwe_token = token.serialize()
        return jwe_token

    @classmethod
    def check_server_details(cls, user_id, serverId):
        server = storage.get('Server', serverId)
        if (server is None or server.get('serverId') != serverId or
            server.get('userId') != user_id):
            return None
        return server.to_dict()
