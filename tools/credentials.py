from typing import Dict, Any
from tools.registry import registry
from storage.models import RiskLevel
from storage.credentials import credential_vault

@registry.register(
    name="store_vault_credential",
    description="Stores encrypted platform credentials, passwords, or API keys in the local secure AES-256 Vault.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "service_name": {"type": "string", "description": "Service or platform name (e.g. 'github', 'apify', 'aws', 'instagram')"},
            "username": {"type": "string", "description": "Username or login email"},
            "secret": {"type": "string", "description": "Password, API key, or authentication token to encrypt"},
            "metadata": {"type": "object", "description": "Optional metadata payload"}
        },
        "required": ["service_name", "username", "secret"]
    }
)
def store_vault_credential(service_name: str, username: str, secret: str, metadata: dict = None) -> Dict[str, Any]:
    try:
        msg = credential_vault.save_credential(service_name, username, secret, metadata)
        return {"success": True, "output": msg}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="get_vault_credential",
    description="Retrieves decrypted login credentials or API key for a specified service from the encrypted vault.",
    risk_level=RiskLevel.HIGH,
    schema={
        "type": "object",
        "properties": {
            "service_name": {"type": "string", "description": "Service name to look up"}
        },
        "required": ["service_name"]
    }
)
def get_vault_credential(service_name: str) -> Dict[str, Any]:
    try:
        cred = credential_vault.get_credential(service_name)
        if cred:
            return {
                "success": True,
                "service_name": cred["service_name"],
                "username": cred["username"],
                "secret": cred["secret"],
                "metadata": cred.get("metadata", {})
            }
        return {"success": False, "output": f"No credential found in vault for service '{service_name}'."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="list_vault_credentials",
    description="Lists all services stored in the local encrypted credential vault (with secrets masked).",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_vault_credentials() -> Dict[str, Any]:
    try:
        creds = credential_vault.list_credentials()
        if creds:
            formatted = "\n".join([f"- Service: '{c['service_name']}' | User: {c['username']} | Secret: {c['secret_masked']}" for c in creds])
            return {"success": True, "output": f"Encrypted Vault Credentials ({len(creds)}):\n{formatted}", "credentials": creds}
        return {"success": True, "output": "Encrypted credential vault is currently empty.", "credentials": []}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="delete_vault_credential",
    description="Deletes credentials for a specific service from the encrypted vault.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "service_name": {"type": "string", "description": "Service name to remove from vault"}
        },
        "required": ["service_name"]
    }
)
def delete_vault_credential(service_name: str) -> Dict[str, Any]:
    try:
        msg = credential_vault.delete_credential(service_name)
        return {"success": True, "output": msg}
    except Exception as e:
        return {"success": False, "error": str(e)}
