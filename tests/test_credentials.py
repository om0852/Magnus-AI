import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from storage.credentials import credential_vault
from tools.credentials import store_vault_credential, get_vault_credential, list_vault_credentials, delete_vault_credential

class TestCredentialVault(unittest.TestCase):
    def test_vault_encryption(self):
        service = "github_test"
        user = "dev_user"
        secret = "super_secret_token_12345"

        # Save credential
        res = store_vault_credential(service, user, secret, {"env": "prod"})
        self.assertTrue(res["success"])

        # List credentials
        list_res = list_vault_credentials()
        self.assertTrue(list_res["success"])
        self.assertGreaterEqual(len(list_res["credentials"]), 1)

        # Get credential
        get_res = get_vault_credential(service)
        self.assertTrue(get_res["success"])
        self.assertEqual(get_res["username"], user)
        self.assertEqual(get_res["secret"], secret)

        # Delete credential
        del_res = delete_vault_credential(service)
        self.assertTrue(del_res["success"])

        # Verify deletion
        get_res_after = get_vault_credential(service)
        self.assertFalse(get_res_after["success"])

if __name__ == "__main__":
    unittest.main()
