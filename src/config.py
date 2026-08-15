"""Shared configuration for the SEC Disclosure Integrity Platform."""

CATALOG = "sec_dev"

SCHEMA_LANDING = f"{CATALOG}.landing"
SCHEMA_BRONZE  = f"{CATALOG}.bronze"
SCHEMA_SILVER  = f"{CATALOG}.silver"
SCHEMA_GOLD    = f"{CATALOG}.gold"

RAW_VOLUME = f"/Volumes/{CATALOG}/landing/raw"

SEC_BASE_URL = (
    "https://www.sec.gov/files/dera/data/"
    "financial-statement-data-sets"
)

SEC_USER_AGENT = "Atif Memon atifm1726@gmail.com"

SOURCE_FILES = ["sub.txt", "tag.txt", "num.txt", "pre.txt"]

QUARTERS = [
    "2024q2", "2024q3", "2024q4",
    "2025q1", "2025q2", "2025q3", "2025q4",
    "2026q1",
]
