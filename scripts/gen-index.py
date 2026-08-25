#!/usr/bin/env python3
"""Generate index.json for the Paradox Computer Basecamp repository.

Reads every *.lgx in ../lgx/, and for each emits a package/version entry in the
schemaVersion-2 format Basecamp's package_downloader expects: download url, file
sha256, rootHash (== manifest.hashes.root), and the embedded manifest (which
carries display_name, per-variant hashes, dependencies, view, etc.).

Packages too large to live in the repository are described by a JSON file in
../external/ instead (see EXTERNAL_DIR below). GitHub refuses any file over
100 MB, and Pages cannot serve a Git-LFS pointer as its payload, so a package
that exceeds the limit is uploaded to a GitHub release and named here by its
absolute url. Everything the index needs is captured in the sidecar, so the
index still regenerates on a clean checkout with no large blob present.

Usage:
  gen-index.py --base-url https://packages.paradox.computer/lgx [--repo-name paradox-modules] > index.json

The download url for each package is  <base-url>/<lgx filename>.  Point --base-url
at wherever the .lgx files are actually served (a static dir on netcup, GitHub
release assets, etc.); it must match where paradox-repo.json's consumers fetch.
"""
import argparse
import datetime
import gzip
import hashlib
import io
import json
import os
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
LGX_DIR = os.path.join(HERE, "..", "lgx")
EXTERNAL_DIR = os.path.join(HERE, "..", "external")


def read_manifest(path):
    with gzip.open(path, "rb") as gz:
        with tarfile.open(fileobj=io.BytesIO(gz.read())) as tf:
            m = tf.extractfile("manifest.json")
            return json.load(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True,
                    help="URL prefix the .lgx files are served from (no trailing slash needed)")
    ap.add_argument("--repo-name", default="paradox-modules")
    ap.add_argument("--generated-at", default=None,
                    help="ISO8601 timestamp; defaults to now (UTC)")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    gen_at = args.generated_at or datetime.datetime.now(
        datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    packages = []

    # Externally-hosted packages first; each sidecar carries the absolute url, the
    # size/sha256 of the asset and the manifest lifted from it at upload time.
    for fn in sorted(os.listdir(EXTERNAL_DIR)) if os.path.isdir(EXTERNAL_DIR) else []:
        if not fn.endswith(".json"):
            continue
        ext = json.load(open(os.path.join(EXTERNAL_DIR, fn)))
        manifest = ext["manifest"]
        packages.append({
            "name": manifest["name"],
            "versions": [{
                "releasedAt": gen_at,
                "publisherRef": "%s-v%s" % (manifest["name"], manifest.get("version", "0")),
                "url": ext["url"],
                "size": ext["size"],
                "sha256": ext["sha256"],
                "rootHash": manifest.get("hashes", {}).get("root", ""),
                "manifest": manifest,
            }],
        })

    for fn in sorted(os.listdir(LGX_DIR)):
        if not fn.endswith(".lgx"):
            continue
        path = os.path.join(LGX_DIR, fn)
        manifest = read_manifest(path)
        data = open(path, "rb").read()
        packages.append({
            "name": manifest["name"],
            "versions": [{
                "releasedAt": gen_at,
                "publisherRef": "%s-v%s" % (manifest["name"], manifest.get("version", "0")),
                "url": "%s/%s" % (base, fn),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "rootHash": manifest.get("hashes", {}).get("root", ""),
                "manifest": manifest,
            }],
        })

    names = [p["name"] for p in packages]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        sys.exit("error: %s described both in lgx/ and external/" % ", ".join(dupes))
    packages.sort(key=lambda p: p["name"])

    index = {
        "schemaVersion": 2,
        "repositoryName": args.repo_name,
        "generatedAt": gen_at,
        "packages": packages,
    }
    json.dump(index, sys.stdout, indent=2)
    sys.stdout.write("\n")
    print("wrote %d package(s): %s" % (len(packages), ", ".join(p["name"] for p in packages)),
          file=sys.stderr)


if __name__ == "__main__":
    main()
