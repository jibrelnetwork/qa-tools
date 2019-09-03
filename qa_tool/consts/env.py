import os

DISABLE_SCHEMA_VALIDATOR = os.environ("DISABLE_SCHEMA_VALIDATOR", False)


if DISABLE_SCHEMA_VALIDATOR:
    for _ in range(5):
        print('Now You disable schema validator!!!!!!!!   DANGER!!!!')
