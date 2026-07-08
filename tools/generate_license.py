#!/usr/bin/env python
"""License key generator for Sjursen Digital.

This tool uses our private RSA key to generate signed JWT license keys for self-hosters.
It is kept in the monorepo tools directory for the developer's convenience.

Usage:
    python generate_license.py "<customer-name>" "<customer-email>" "<modules-comma-separated>" [expiry-days]

Example:
    python generate_license.py "Acme Corp" "admin@acme.com" "komfyrvakt,obsero" 365
"""
import sys
import time

try:
    import jwt
except ImportError:
    print("Error: 'pyjwt' with 'cryptography' is required. Install it using:")
    print("  pip install pyjwt[crypto]")
    sys.exit(1)

# Hardcoded Sjursen Digital RSA Private Key
PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDMD4p285sN9tFK
jAvadIMZtwlscqfRD/24b6wocMR5hiK0Tfiin6AVYjK2qkiDX0Vwbz5ztaKRlJKR
+myvx5ESMd+Ew0lt2tS3yf/9ltgZLiYiRgEKh9NqH0n8jEikks7+cBVLLhCnwgSO
3RfCHeAuDCn1nO/gpxCy7VRxiouxXwaX0DbUr4qjgapnXEkgsvAEQsICeEF1egLo
kDB2BkSTnjMIZAHzRPKbyw1oGGzAZ1zP+Fg/rdUgD3AhU5bfI4oah4L0CwddctSA
B+B5uF9W15o6sZJ4el59QEiMn4JJWRkv5Ejh7leUo9/eLnRCPR/1/776hYyiMtf0
DBLAXU0VAgMBAAECggEAL3liHmB4b1w/vtcsHsvCgGYMBDX8gu/0eEdKxzHNE/S3
+Di3oqX+aVsqL0MYka/FiO3omqTkSHhHTTz0skR8pL4DoXCJkcw6dvPA4a+JYPpS
luCwd1G4RtU2slG0yMz66UkMOyxhZZYG13HqiBfJQw1Dacf0KtDTWr1KSwwPidkG
UBwjx1aNmow4nhxTECSJkIJ/cT+V4ba3mpG+cfr4xBaDXjnZAzwweTPLzeiMxngH
k3WexJAFBsiQkYdHJ/7o01Z4X4LBQe++WYXBTBPer1SywOOAIaJBjoWAVRiunXZ7
SMR9nKAi+v7nS2sqcR4rOLDrtPaJrj+7wukHC5YoQQKBgQDuLkq0ybriCe3J9Sy6
Ezk05Xg5nqesMffrNtpmKDRrT8Dz5y3oFZYGS+bgSyrIKJACuKpqMnCQIfG1PN0+
T5r75ygxK1VOrEuDpTczoz1kZ4whNzkEzoSetqmSLbbH0gE3fef8ZrQJYiVtUyZ1
Jyx3BKeOIvscQnJAtbEPXX4kcQKBgQDbU8VHa5PhhFdLgvF/1TfifhMM5v79LFPh
cLWfQjGkFu3T4N4iG8lsQ3ZIycb/Sx0Dfu4fCtvTfojLkEMXPgQVeZ4WBy8aA1u6
4VyOpuCdfnVUSJeDnwGZjFezhe3jR9voOPLoG4+9lMTTuCOEmYkKNe4WP41IUPQE
2xy9Ofv05QKBgDGX9fo63uzeAGNC57M++XRoK2ZkAKm8JdEWNNd8m52Ul6qxgj+G
7xwUhdhCDoBq4cGPTfya0BFS4A9Kww6MaMr20MmcKkEdYwPgTOQ1ozzayrTH2NmF
XtvlUN2dIyfsNFCnqLxHbkld5EklPSa7p2iI0ZKo+fxiYYPT0TBP2UohAoGAYtvr
fDm9OlVQk7S97gTJX8m8BIDKRouIc4E+HD7V6UR8hphBB9bGf4oY8s4gaEoPFdhM
tKlMVJQgTMEFvKAzbwqWew9Z57vDyQRzl8kYTWUGtarSwH0XV4KutTiU9XEaah3h
P0XNEILSBSxmtgoOfw+39UdIA2SZ2OZ6mcBdFRECgYAdca9aw83j8hSoK77ndpva
CXI9R27hBN25ymlArg4VTjc4fJd/Fim5k5TR+GFvanLYrSJuMKgOFRO1Av3C1fAY
BW+dnfHSL1OxixAOLSMqygr6aT5fCnlznFPUpk0RR3kiG6vLxmvfAliNZQ2fn5am
4eyOlVKJiy99dFqHy4JcHA==
-----END PRIVATE KEY-----"""


def main():
    if len(sys.argv) < 4:
        print("Usage: python generate_license.py \"<customer-name>\" \"<customer-email>\" \"<modules-comma-separated>\" [expiry-days]")
        sys.exit(1)

    customer = sys.argv[1]
    email = sys.argv[2]
    modules_str = sys.argv[3]
    expiry_days = int(sys.argv[4]) if len(sys.argv) > 4 else None

    modules = {name.strip(): True for name in modules_str.split(",") if name.strip()}

    now = int(time.time())
    payload = {
        "iss": "Sjursen Digital",
        "iat": now,
        "sub": customer,
        "email": email,
        "modules": modules,
    }

    if expiry_days:
        payload["exp"] = now + (expiry_days * 86400)

    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

    print("\n" + "=" * 80)
    print(f" LICENSE KEY GENERATED FOR: {customer}")
    print(f" Modules enabled: {', '.join(modules.keys())}")
    print(f" Expires: {f'In {expiry_days} days' if expiry_days else 'Never (Lifetime)'}")
    print("=" * 80)
    print("\nCopy and paste this key into the Gateway licensing portal:")
    print(token)
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
