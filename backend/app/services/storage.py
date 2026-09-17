"""S3-compatible object storage (Backblaze B2, Cloudflare R2, or any S3 provider).

Required env vars:
  STORAGE_ENDPOINT    — full endpoint URL  (e.g. https://s3.us-east-005.backblazeb2.com)
  STORAGE_ACCESS_KEY  — access key / key ID
  STORAGE_SECRET_KEY  — secret access key / application key
  STORAGE_BUCKET      — bucket name
  STORAGE_PUBLIC_URL  — (optional) public base URL; leave empty for private buckets

When STORAGE_ENDPOINT is absent, is_enabled() returns False and callers fall back
to local disk storage.

When STORAGE_PUBLIC_URL is set (public bucket), uploaded files get a permanent
public URL. When it is absent (private bucket), callers use signed_url() to
generate time-limited download links.
"""
import os
import re
import tempfile
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

SIGNED_URL_EXPIRY = 24 * 3600  # 24 hours


def is_enabled() -> bool:
    return bool(os.environ.get("STORAGE_ENDPOINT"))


def is_public_mode() -> bool:
    return bool(os.environ.get("STORAGE_PUBLIC_URL"))


def _region() -> str:
    endpoint = os.environ.get("STORAGE_ENDPOINT", "")
    m = re.search(r"s3\.([^.]+)\.backblazeb2\.com", endpoint)
    return m.group(1) if m else "auto"


def _client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["STORAGE_ENDPOINT"],
        aws_access_key_id=os.environ["STORAGE_ACCESS_KEY"],
        aws_secret_access_key=os.environ["STORAGE_SECRET_KEY"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name=_region(),
    )


def _bucket() -> str:
    return os.environ["STORAGE_BUCKET"]


def upload(local_path: str | Path, key: str) -> str:
    """Upload a local file. Returns public URL (public mode) or the key (private mode)."""
    _client().upload_file(str(local_path), _bucket(), key)
    if is_public_mode():
        return f"{os.environ['STORAGE_PUBLIC_URL'].rstrip('/')}/{key}"
    return key


def signed_url(key: str, expires: int = SIGNED_URL_EXPIRY) -> str:
    """Generate a time-limited download URL for a private object."""
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket(), "Key": key},
        ExpiresIn=expires,
    )


def public_url(key: str) -> str:
    base = os.environ.get("STORAGE_PUBLIC_URL", "").rstrip("/")
    if base:
        return f"{base}/{key}"
    return signed_url(key)


def delete(key: str) -> None:
    try:
        _client().delete_object(Bucket=_bucket(), Key=key)
    except ClientError:
        pass


def delete_prefix(prefix: str) -> None:
    """Delete all objects whose key starts with prefix (for job cleanup)."""
    client = _client()
    bucket = _bucket()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
        if objects:
            client.delete_objects(Bucket=bucket, Delete={"Objects": objects})


def download(key: str, local_path: str | Path) -> None:
    _client().download_file(_bucket(), key, str(local_path))


def download_to_temp(key: str) -> Path:
    """Download an object to a new temp file. Caller must delete it."""
    tmp = Path(tempfile.mkdtemp()) / Path(key).name
    download(key, tmp)
    return tmp


def resolve_url(value: str | None) -> str | None:
    """Convert a stored key to a usable URL. Passes through local /files/ paths unchanged."""
    if not value or not is_enabled():
        return value
    # Already a full URL (public mode or old entries) — leave as-is
    if value.startswith("/") or value.startswith("http"):
        return value
    # It's a bare storage key — generate signed URL
    return signed_url(value)


def key_from_url(url: str) -> str | None:
    """Extract object key from a public URL."""
    base = os.environ.get("STORAGE_PUBLIC_URL", "").rstrip("/")
    if base and url.startswith(base):
        return url[len(base):].lstrip("/").split("?")[0]
    return None


def key_from_value(value: str | None) -> str | None:
    """Return the storage key whether value is a bare key or a full URL."""
    if not value:
        return None
    if value.startswith("/") or not value.startswith("http"):
        # bare key or local path — bare key doesn't start with /
        if not value.startswith("/"):
            return value
        return None
    return key_from_url(value)
