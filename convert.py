from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
import time

client_id = "sk-kKlDSq1YTeGQuTcG0HBWmr_EpA2MoFm2LEDmqBQoMhNaQxh6muXto2NcWHQzWeIK"
client_secret = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCLoYjN/jGD+gqeqo34Q1h38yQ69nfwFjLM7z4rK8id0i4SIquwCk+Hz9QkUsjhM5tcOX/h4oVVnkt941icmWj0TNCJ3Ii5DAlFHfTe+3LiyznRsmnnK5FhBraFCuaEVmBdsXyo1Ol+9u9XZEnJNi65Q334K0eWvXEOnuz1VwQydwIDAQAB"

# Format public key
public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{client_secret}\n-----END PUBLIC KEY-----"

# Load public key
public_key = serialization.load_pem_public_key(
    public_key_pem.encode(),
    backend=default_backend()
)

# Create data string
timestamp = int(time.time() * 1000)  # milliseconds
data = f"client_id={client_id}&timestamp={timestamp}"

# Encrypt data
encrypted = public_key.encrypt(
    data.encode(),
    padding.PKCS1v15()
)

# Convert to base64 and print
print(base64.b64encode(encrypted).decode())
