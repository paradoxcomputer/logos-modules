# Paradox Computer module repository for Logos Basecamp

Add this repository in Logos Basecamp (Settings, Repositories, Add a repository):

```
https://paradoxcomputer.github.io/logos-modules/repo.json
```

Then open the Package Manager and install:

| App | Package | What it is |
|---|---|---|
| **Medusa** | `medusa_ui` | Privacy wallet. Its `medusa_core` backend is pulled in automatically. |
| **ZoneScan Lite** | `zonescan_lite` | Block explorer for Logos Execution Zones. No dependencies. |
| **Tip Jar** | `tip_jar` | Optional "Connect with Medusa" demo. |

Basecamp picks the build for your platform automatically.

Learn more at https://medusa.paradox.computer

## Maintaining this repository

Regenerate `index.json` after changing anything under `lgx/` or `external/`:

```
python3 scripts/gen-index.py --base-url https://paradoxcomputer.github.io/logos-modules/lgx > index.json
```

Redirect stdout only — the script writes its summary to stderr, and `2>&1` corrupts the file.

### Variant names

Basecamp resolves variants by name and accepts exactly one spelling: a portable build (the
AppImage) takes the plain name, a build from source takes the `-dev` name and nothing else —
`platformVariantsToTry()` *replaces* its candidate list with the `-dev` forms unless the host
was compiled with `LGPM_PORTABLE_BUILD`. A package missing a spelling is uninstallable for
that half of the audience, with `Package does not contain variant for platform: …`.

So a package should carry every platform twice, e.g. `linux-amd64` **and** `linux-amd64-dev`,
with the same portable payload under both. The release workflows do this after `lgx merge`.

### Size limits

Two ceilings apply, and they pull against carrying both spellings, since a second name means a
second full copy of the payload:

- GitHub refuses any file over **100 MB** in a repository. A larger payload goes on the
  `packages` release instead of into `lgx/`, described by a sidecar in `external/` carrying the
  url, size, sha256 and manifest. Git LFS is not an option: Pages serves the LFS pointer rather
  than the file. The sidecar holds everything `index.json` needs, so the index still
  regenerates on a clean checkout with no large file present.
- Basecamp's downloader has a hard **600-second** total timeout
  (`CURLOPT_TIMEOUT` in `package_downloader_lib.cpp`), with no resume. At a measured ~240 kB/s
  that is about **140 MB**, whatever the hosting.

`medusa_core` is why this is written down. It is 84 MB with one spelling and 167 MB with both;
the second form takes ~720 s to fetch and so cannot be installed at all on an ordinary
connection. It therefore ships with the plain names only, and is not installable from a
source build of Basecamp until its payload is smaller. Stripping its binaries recovers only
15–24 % — they are already close to stripped — so the saving has to come from the four Rust
binaries under `bin/` that make up 112 MB of the 128 MB variant.
