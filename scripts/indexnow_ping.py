#!/usr/bin/env python3
"""Ping IndexNow (Bing + participating engines) with every URL in sitemap.xml.
Run after each production deploy. Docs: https://www.indexnow.org/documentation
"""
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOST = "dateme.mhndlabs.com"
KEY = "1337177ce2c7fa996ce2ae82004e2355"  # served at /<KEY>.txt

urls = re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text())
payload = json.dumps({"host": HOST, "key": KEY, "urlList": urls}).encode()
req = urllib.request.Request(
    "https://api.indexnow.org/indexnow", data=payload,
    headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req) as resp:
    print(f"IndexNow: HTTP {resp.status} for {len(urls)} urls")
