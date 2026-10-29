# Day 1: API Data Extraction and Transformation

## 1. Overview

This script pulls customer records from the JSONPlaceholder Users API
(`https://jsonplaceholder.typicode.com/users`), flattens the nested JSON,
and exports a clean CSV that the analytics team can load and join against
their sales data.

Steps the script performs:

1. Fetches the users with `requests.get()`, using a timeout and checking the status code.
2. Prints the structure of the payload and of one record.
3. Extracts core fields (id, name, email, city, company).
4. Builds a list of names, a list of `(id, email)` tuples and an `id -> city` dict.
5. Flattens each record into single-level, underscore-joined keys.
6. Loads the records into a pandas DataFrame, renames `id` to `customer_id`,
   converts coordinates to numbers and orders the columns to match
   `expected_customers_clean.csv`.
7. Writes `output/customers_clean.csv` without the index, overwriting any previous run.
8. Handles request failures with one clear message and a non-zero exit code.

## 2. How to run

Commands are for Git Bash on Windows.

```bash
# 1. Create the virtual environment (first time only)
python -m venv APIDemo

# 2. Activate it
source APIDemo/Scripts/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the script
python extract_customers.py
```

Optional arguments, used for testing failures:

```bash
python extract_customers.py --url <api-url> --timeout <seconds>
```

The output is written to `output/customers_clean.csv`. Re-running the script
overwrites the file rather than appending to it.

## 3. Data structure findings

- The top-level payload is a **list** of 10 **dicts** (one per user).
- Each record has simple fields (`id`, `name`, `username`, `email`, `phone`, `website`)
  and two nested dicts:

| Field | Type | Nesting depth |
|---|---|---|
| `address` | dict | 1 level |
| `address.geo` | dict | 2 levels (inside `address`) |
| `company` | dict | 1 level |

- `address` holds `street`, `suite`, `city`, `zipcode` and the nested `geo` dict.
- `geo` holds `lat` and `lng`, which the API returns as **strings**.
- `company` holds `name`, `catchPhrase` and `bs`.

## 4. Assumptions

- **Missing text fields** (name, email, city, company name) default to `"Unknown"`.
- **A missing `id`** stays `None` rather than being invented.
- **Missing or `null` nested objects** (for example no `address`) do not crash
  the script; their fields fall back to the defaults above.
- **Coordinates** are converted with `pd.to_numeric(errors="coerce")`, so the
  values become floats and any unparseable value becomes `NaN`.
- **Lists inside records** (none exist in this API) are left as they are by
  `flatten_user`; only dicts are flattened.
- **A 200 response that is not a list of dicts** is treated as an error and
  reported with a clear message.
- **Column names**: `catchPhrase` is renamed to `company_catchphrase` (lowercase)
  to match the expected CSV header.

## 5. Failure testing

Each failure produces one clear message on stderr and exit code `1`, with no traceback.

| Case | Command | Message | Exit code |
|---|---|---|---|
| Wrong URL | `python extract_customers.py --url https://jsonplaceholdr.typicode.com/users` | `ERROR: Could not connect to https://jsonplaceholdr.typicode.com/users (bad host or no network).` | 1 |
| Non-200 response | `python extract_customers.py --url https://jsonplaceholder.typicode.com/userz` | `ERROR: Unexpected HTTP status 404 from https://jsonplaceholder.typicode.com/userz` | 1 |
| Timeout | `python extract_customers.py --timeout 0.001` | `ERROR: Request timed out after 0.001s: https://jsonplaceholder.typicode.com/users` | 1 |
| Body not JSON | `python extract_customers.py --url https://example.com` | `ERROR: Response body is not valid JSON.` | 1 |

Exit codes were checked with `echo $?` straight after each command.

### Flatten test on unseen, deeper data

`flatten_user` does not hard-code any field names. A made-up record with
four levels of nesting:

```bash
python -c "from extract_customers import flatten_user; print(flatten_user({'a': {'b': {'c': {'d': 1}}}, 'x': 2}))"
```

Output:

```
{'a_b_c_d': 1, 'x': 2}
```

## Project structure

```
day1-api-extraction/
├── extract_customers.py
├── output/
│   └── customers_clean.csv
├── requirements.txt
└── README.md
```
