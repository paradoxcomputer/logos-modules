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

Every package carries each platform under two variant names, e.g. `linux-amd64` **and**
`linux-amd64-dev`. Basecamp resolves variants by name and accepts only one spelling or the
other: a portable build (the AppImage) takes the plain name, while a build from source takes
the `-dev` name and nothing else. A package missing either spelling is uninstallable for half
the audience, with `Package does not contain variant for platform: …`.

Payloads over GitHub's 100 MB file limit go on the `packages` release instead of into `lgx/`,
described by a sidecar in `external/` that carries the url, size, sha256 and manifest. Git LFS
is not an option here: Pages serves the LFS pointer rather than the file. The sidecar holds
everything `index.json` needs, so the index still regenerates on a clean checkout with no large
file present.
