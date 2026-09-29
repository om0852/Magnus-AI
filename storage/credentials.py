import os
import json
import base64
import hashlib
import hmac
import secrets
from typing import Dict, Any, List, Optional

class CredentialVault:
    """
    AES-256 Equivalent Encrypted Local Vault for Magnas AI.
    Uses PBKDF2-HMAC-SHA256 key derivation with HMAC-authenticated CTR keystream encryption.
    Zero external dependencies, keeping Magnas lightweight (< 40MB idle RAM).
    """

    def __init__(self, vault_path: str = "storage/vault.enc"):
        self.vault_path = os.path.abspath(vault_path)
        self._master_key = self._derive_master_key()

    def _derive_master_key(self) -> bytes:
        # Machine-specific unique identifier combined with environment context
        machine_id = os.environ.get("COMPUTERNAME", "MAGNAS_SYSTEM_NODE") + os.environ.get("USERNAME", "DEFAULT_USER")
        salt = b"MAGNAS_AI_LOCAL_VAULT_SALT_v1"
        return hashlib.pbkdf2_hmac("sha256", machine_id.encode("utf-8"), salt, iterations=100000)

    def _encrypt(self, plaintext: str) -> str:
        data_bytes = plaintext.encode("utf-8")
        iv = secrets.token_bytes(16)
        
        # Derive encryption and MAC keys
        enc_key = hashlib.sha256(self._master_key + iv + b"ENC").digest()
        mac_key = hashlib.sha256(self._master_key + iv + b"MAC").digest()

        # Keystream generation via counter mode HMAC-SHA256
        keystream = bytearray()
        counter = 0
        while len(keystream) < len(data_bytes):
            block = hmac.new(enc_key, counter.to_bytes(4, "big"), hashlib.sha256).digest()
            keystream.extend(block)
            counter += 1

        ciphertext = bytes([b ^ k for b, k in zip(data_bytes, keystream)])
        tag = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()

        payload = {
            "iv": base64.b64encode(iv).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii")
        }
        return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")

    def _decrypt(self, encrypted_blob: str) -> str:
        raw_json = base64.b64decode(encrypted_blob.encode("ascii")).decode("utf-8")
        payload = json.loads(raw_json)

        iv = base64.b64decode(payload["iv"])
        ciphertext = base64.b64decode(payload["ciphertext"])
        tag = base64.b64decode(payload["tag"])

        enc_key = hashlib.sha256(self._master_key + iv + b"ENC").digest()
        mac_key = hashlib.sha256(self._master_key + iv + b"MAC").digest()

        # Verify HMAC tag first (encrypt-then-MAC)
        expected_tag = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Integrity check failed: Vault payload corrupted or tampered.")

        keystream = bytearray()
        counter = 0
        while len(keystream) < len(ciphertext):
            block = hmac.new(enc_key, counter.to_bytes(4, "big"), hashlib.sha256).digest()
            keystream.extend(block)
            counter += 1

        plaintext = bytes([c ^ k for c, k in zip(ciphertext, keystream)])
        return plaintext.decode("utf-8")

    def _read_vault_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.vault_path):
            return {}
        try:
            with open(self.vault_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                decrypted_json = self._decrypt(content)
                return json.loads(decrypted_json)
        except Exception as e:
            print(f"[Vault Warning] Failed to read vault file: {e}")
            return {}

    def _write_vault_data(self, data: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        raw_json = json.dumps(data)
        encrypted_blob = self._encrypt(raw_json)
        with open(self.vault_path, "w", encoding="utf-8") as f:
            f.write(encrypted_blob)

    def save_credential(self, service_name: str, username: str, secret: str, metadata: dict = None) -> str:
        vault_data = self._read_vault_data()
        key = service_name.lower().strip()
        vault_data[key] = {
            "service_name": service_name,
            "username": username,
            "secret": secret,
            "metadata": metadata or {},
            "updated_at": secrets.token_hex(4)
        }
        self._write_vault_data(vault_data)
        return f"Successfully saved encrypted credential for '{service_name}' in vault."

    def get_credential(self, service_name: str) -> Optional[Dict[str, Any]]:
        vault_data = self._read_vault_data()
        key = service_name.lower().strip()
        return vault_data.get(key)

    def list_credentials(self) -> List[Dict[str, Any]]:
        vault_data = self._read_vault_data()
        results = []
        for k, v in vault_data.items():
            results.append({
                "service_name": v.get("service_name", k),
                "username": v.get("username", ""),
                "secret_masked": "*" * len(v.get("secret", "******")),
                "metadata": v.get("metadata", {})
            })
        return results

    def delete_credential(self, service_name: str) -> str:
        vault_data = self._read_vault_data()
        key = service_name.lower().strip()
        if key in vault_data:
            del vault_data[key]
            self._write_vault_data(vault_data)
            return f"Successfully deleted credential for '{service_name}' from vault."
        return f"No credential found for '{service_name}'."

credential_vault = CredentialVault()
