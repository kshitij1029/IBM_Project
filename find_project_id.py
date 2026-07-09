"""
find_project_id.py
───────────────────
Run this script to list all Watsonx.ai projects associated with your
IBM API Key, so you can copy the correct WATSONX_PROJECT_ID into .env

Usage:
    python find_project_id.py
"""

import os
from dotenv import load_dotenv

load_dotenv(".env")

IBM_API_KEY = os.getenv("IBM_API_KEY", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://au-syd.ml/.cloud.ibm.com")

if not IBM_API_KEY:
    print("ERROR: IBM_API_KEY not set in .env")
    exit(1)

print(f"Using URL  : {WATSONX_URL}")
print(f"API Key    : {IBM_API_KEY[:8]}...")
print()

# ── Step 1: Get IAM token ────────────────────────────────────────────────────
import requests

iam_resp = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    data={
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": IBM_API_KEY,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=15,
)

if iam_resp.status_code != 200:
    print(f"ERROR: Could not get IAM token (HTTP {iam_resp.status_code})")
    print(iam_resp.text)
    exit(1)

token = iam_resp.json()["access_token"]
print("IAM token obtained successfully.\n")

# ── Step 2: List Watsonx projects ────────────────────────────────────────────
# Projects are managed via the IBM Cloud API (not the Watsonx URL)
proj_resp = requests.get(
    "https://api.dataplatform.cloud.ibm.com/v2/projects",
    headers={"Authorization": f"Bearer {token}"},
    params={"limit": 20},
    timeout=15,
)

if proj_resp.status_code != 200:
    print(f"ERROR: Could not list projects (HTTP {proj_resp.status_code})")
    print(proj_resp.text)
    exit(1)

projects = proj_resp.json().get("resources", [])

if not projects:
    print("No Watsonx.ai projects found for this API key.")
    print()
    print("Create one at: https://dataplatform.cloud.ibm.com/projects/?context=wx")
    exit(1)

print(f"Found {len(projects)} project(s):\n")
print(f"{'Name':<40}  {'Project ID':<38}  {'Created'}")
print("-" * 95)
for p in projects:
    name    = p.get("entity", {}).get("name", "—")
    pid     = p.get("metadata", {}).get("guid", "—")
    created = p.get("metadata", {}).get("created_at", "—")[:10]
    print(f"{name:<40}  {pid:<38}  {created}")

print()
print("─" * 60)
print("Copy the Project ID of your Watsonx.ai project above and")
print("update WATSONX_PROJECT_ID in your .env file.")
