from cryptography.fernet import Fernet

# # Generate a key
# encryption_key = Fernet.generate_key()

# # Save this key to a file or environment variable for future use
# with open("secret.key", "wb") as key_file:
#     key_file.write(encryption_key)

# print(encryption_key)


# Load the key (from file or any secure storage)
with open("secret.key", "rb") as key_file:
    key = key_file.read()

# Create a Fernet instance with the key
cipher_suite = Fernet(key)

# Your SMTP credentials
smtp_username = "customappsmtp@datanetiix.com"
smtp_password = "Vom71445"

# Encrypt the credentials
encrypted_username = cipher_suite.encrypt(smtp_username.encode())
encrypted_password = cipher_suite.encrypt(smtp_password.encode())

# Print the encrypted credentials (for demonstration)
print(encrypted_username)
print(encrypted_password)



