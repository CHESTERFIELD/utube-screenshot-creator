#!/usr/bin/env python3

import json
import os
import shutil
import ssl
import sys
import urllib.request
import zipfile

import logging

JSON_URL = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
PLATFORM = "mac-arm64"
TARGET_FILENAME = "chromedriver.exe"


def _ssl_context() -> ssl.SSLContext:
    if os.environ.get("CHROMEDRIVER_INSECURE_SSL") == "1":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    ctx = ssl.create_default_context()
    try:
        import certifi  # type: ignore

        ctx.load_verify_locations(certifi.where())
    except Exception:
        pass
    return ctx


def _http_get_json(url: str) -> dict:
    with urllib.request.urlopen(url, context=_ssl_context()) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        body = resp.read().decode(charset)
    return json.loads(body)


def _download_file(url: str, dest_path: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
    with urllib.request.urlopen(req, context=_ssl_context()) as resp, open(dest_path, "wb") as f:
        shutil.copyfileobj(resp, f)


def _find_chromedriver_zip_url(payload: dict) -> str:
    try:
        items = payload["channels"]["Stable"]["downloads"]["chromedriver"]
    except KeyError as e:
        raise RuntimeError("Unexpected JSON structure: missing Stable chromedriver downloads") from e

    for item in items:
        if item.get("platform") == PLATFORM and item.get("url"):
            return item["url"]

    raise RuntimeError(f"Could not find chromedriver download for platform={PLATFORM}")


def _extract_single_file(zip_path: str, dest_path: str) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [i for i in zf.infolist() if not i.is_dir()]
        if not members:
            raise RuntimeError("Zip archive contains no files")

        def _basename(info: zipfile.ZipInfo) -> str:
            return os.path.basename(info.filename.rstrip("/"))

        preferred = [i for i in members if _basename(i) in {"chromedriver", "chromedriver.exe"}]
        if len(preferred) == 1:
            member_info = preferred[0]
        elif len(members) == 1:
            member_info = members[0]
        else:
            raise RuntimeError(
                "Zip contains multiple files; could not uniquely determine chromedriver binary"
            )

        tmp_path = dest_path + ".tmp"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        with zf.open(member_info, "r") as src, open(tmp_path, "wb") as dst:
            shutil.copyfileobj(src, dst)

        os.replace(tmp_path, dest_path)
        try:
            os.chmod(dest_path, 0o755)
        except OSError:
            pass


def main() -> int:
    while True:
        question = input("Are you sure about updating chromedriver? (y/n): ")
        if question.lower() == "y":
            break
        elif question.lower() == "n":
            logging.warning("Aborted")
            return 0
        else:
            logging.warning("Please enter 'y' or 'n'")
    
    root_dir = os.path.abspath(os.path.dirname(__file__))
    zip_path = os.path.join(root_dir, "chromedriver.zip")
    out_path = os.path.join(root_dir, TARGET_FILENAME)

    try:
        payload = _http_get_json(JSON_URL)
        zip_url = _find_chromedriver_zip_url(payload)

        logging.warning(f"Downloading: {zip_url}")
        _download_file(zip_url, zip_path)

        logging.warning(f"Extracting {TARGET_FILENAME} -> {out_path}")
        _extract_single_file(zip_path, out_path)

        logging.warning("Done")
        return 0
    except Exception as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            logging.warning(
                "ERROR: SSL certificate verification failed. "
                "On macOS this is often fixed by installing/updating CA certs. "
                "Try: `python3 -m pip install --upgrade certifi` and rerun. "
                "As a last resort you can set CHROMEDRIVER_INSECURE_SSL=1 to disable SSL verification.",
                file=sys.stderr,
            )
        logging.warning(f"ERROR: {e}", file=sys.stderr)
        return 1
    finally:
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
