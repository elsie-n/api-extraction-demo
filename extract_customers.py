"""
Day 1 - API Data Extraction and Transformation
Squad Python Specialization - Data Engineering

Fill in every function. Keep the signatures; you may add helpers of your own.
"""
import argparse
import sys
import csv
import json
from pathlib import Path

import pandas as pd
import requests


DEFAULT_URL = "https://jsonplaceholder.typicode.com/users"
OUTPUT_PATH = "output/customers_clean.csv"
MISSING = "Unknown"

COLUMN_ORDER = [
    "customer_id", "name", "username", "email",
    "phone", "website",
    "address_street", "address_suite", "address_city", "address_zipcode",
    "address_geo_lat", "address_geo_lng",
    "company_name", "company_catchphrase", "company_bs",
]

class ExtractionError(Exception):
    """Raised for any expected , user-facing failure."""


def fetch_users(url, timeout=10):
    """Call the users endpoint and return the parsed JSON."""
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.exceptions.Timeout:
        raise ExtractionError(f"Request timed out after {timeout}s: {url}")
    except requests.exceptions.ConnectionError:
        raise ExtractionError(f"Could not connect to {url} (bad host or no network).")
    except requests.exceptions.RequestException as e:
        raise ExtractionError(f"Request failed: {e}")

    if resp.status_code != 200:
        raise ExtractionError(f"Unexpected HTTP status {resp.status_code} from {url}")
    try:
        return resp.json()
    except ValueError:
        raise ExtractionError("Response body is not valid JSON.")


def describe_structure(payload):
    """Print the type of the payload, one record, and every nested value."""
    print(f"Payload: {type(payload).__name__} with {len(payload)} items")
    record = payload[0]
    print(f"One record: {type(record).__name__}")

    def walk(obj, prefix="", depth=1):
        for key, value in obj.items():
            print(f"{'  ' * depth}{prefix}{key}: {type(value).__name__}")
            if isinstance(value, dict):
                walk(value, f"{prefix}{key}.", depth + 1)

    walk(record)


def extract_core_fields(users):
    """Return id, name, email, city, company per user; missing text becomes 'Unknown'."""
    return [
        {
            "id": u.get("id"),
            "name": u.get("name", MISSING),
            "email": u.get("email", MISSING),
            "city": (u.get("address") or {}).get("city", MISSING),
            "company": (u.get("company") or {}).get("name", MISSING),
        }
        for u in users
    ]


def build_structures(users):
    """Return (names list, (id, email) tuples, id->city dict)."""
    core = extract_core_fields(users)
    names = [c["name"] for c in core]
    id_email = [(c["id"], c["email"]) for c in core]
    id_city = {c["id"]: c["city"] for c in core}
    return names, id_email, id_city




def flatten_user(user, parent_key="", sep="_"):
    """Flatten nested dicts of any depth into sep-joined keys."""
    flat = {}
    for key, value in user.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            flat.update(flatten_user(value, new_key, sep))
        else:
            flat[new_key] = value
    return flat


def to_dataframe(flat_users):
    """Build the DataFrame: id renamed, coordinates numeric, fixed column order."""
    df = (
    pd.DataFrame(flat_users)
    .rename(columns={"id": "customer_id", "company_catchPhrase": "company_catchphrase"}))
    for col in ("address_geo_lat", "address_geo_lng"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.reindex(columns=COLUMN_ORDER)
    print("Shape:", df.shape)
    print(df.dtypes)
    return df


def export_csv(df, path):
    """Write the CSV without the index, creating the folder; overwrites each run."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Extract and flatten customer data.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()

    try:
        users = fetch_users(args.url, args.timeout)
        if not isinstance(users, list) or not all(isinstance(u, dict) for u in users):
            raise ExtractionError("JSON was valid but not a list of user objects.")
        describe_structure(users)
        names, id_email, id_city = build_structures(users)
        print(f"{len(names)} users; sample: {id_email[:2]}")
        df = to_dataframe([flatten_user(u) for u in users])
        export_csv(df, OUTPUT_PATH)
        print(f"Wrote {OUTPUT_PATH}")
    except ExtractionError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()