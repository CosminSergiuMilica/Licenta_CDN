from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import os

from utile.mongo_connection import connect_to_mongodb

db, client = connect_to_mongodb()
document = db.origin.find({}, {"domain": 1, "_id": 0})
domains_list = []
if document:
    for doc in document:
        domain = doc.get("domain")
        if domain:
            domains_list.append(domain)
def generate_proxy_certificate(proxy_dir, domains):

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    key_file = os.path.join(proxy_dir, "proxy.key")
    with open(key_file, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, domains[0]),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CosminCDN")
    ])

    alt_names = [x509.DNSName(domain) for domain in domains]
    san = x509.SubjectAlternativeName(alt_names)

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        san, critical=False
    ).sign(
        private_key=key,
        algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    cert_file = os.path.join(proxy_dir, "proxy.crt")
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return key_file, cert_file


generate_proxy_certificate(".", domains_list)

