#!/usr/bin/env python3 

import argparse 
import hashlib 
import json 
import sys 
import time 
from pathlib import Path 
from typing import Any 

import httpx 

SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".txt"}

def sha256_file(file_path: Path) -> str:
    hasher = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)

    return hasher.hexdigest() 

def load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {
            "files": {},
            "created_at": time.time(),
            "update_at": time.time(),
        }