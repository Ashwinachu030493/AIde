import os
import base64
import json
import logging
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class SimpleEncryption:
    """Simplified encryption for SQLite storage using Fernet (AES)"""
    
    def __init__(self):
        self.secret_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.secret_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from file or generate new one"""
        # Store key in user's home directory to persist across server restarts/wipes
        key_dir = os.path.join(os.path.expanduser('~'), '.aide')
        key_file = os.path.join(key_dir, 'encryption.key')
        
        os.makedirs(key_dir, exist_ok=True)
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load encryption key: {e}")
        
        # Generate new key
        new_key = Fernet.generate_key()
        try:
            with open(key_file, 'wb') as f:
                f.write(new_key)
            logger.info(f"Generated new encryption key at {key_file}")
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")
            
        return new_key
    
    def encrypt(self, plaintext: str) -> Optional[str]:
        """Encrypt text and return base64 string for SQLite storage"""
        if not plaintext: return None
        try:
            encrypted = self.cipher_suite.encrypt(plaintext.encode())
            return base64.b64encode(encrypted).decode('ascii')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt(self, encrypted_b64: str) -> Optional[str]:
        """Decrypt base64-encoded encrypted string"""
        if not encrypted_b64: return None
        try:
            encrypted = base64.b64decode(encrypted_b64.encode('ascii'))
            return self.cipher_suite.decrypt(encrypted).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
            
    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Simple API key format validation"""
        validators = {
            'openai': lambda k: k.startswith('sk-') and len(k) > 20,
            'anthropic': lambda k: k.startswith('sk-ant-') and len(k) > 30,
            'groq': lambda k: k.startswith('gsk_') and len(k) > 20,
            'github': lambda k: 'ghp_' in k or 'github_pat_' in k
        }
        if provider not in validators: return True
        return validators[provider](api_key)
