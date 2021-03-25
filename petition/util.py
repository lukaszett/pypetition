import hashlib

def hash_email(email):
    m = hashlib.sha256()
    m.update(email.encode('utf-8'))
    return m.hexdigest()