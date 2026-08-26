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

### Medusa needs the per-architecture files

Install **ZoneScan Lite** from the Package Manager as above. **Medusa** and **Tip Jar** cannot
be installed that way on an ordinary connection: Basecamp abandons a download after 300 seconds
and always fetches every architecture, and `medusa_core` is too large to arrive in time. Worse,
when that deadline fires the install is reported as having *succeeded*.

Download the file for your machine instead, then use **Install LGX Package** in the Package
Manager. Installing from disk does no downloading, so no deadline applies.

| Machine | Files, in this order |
|---|---|
| Linux x86_64 | [medusa_core](https://github.com/paradoxcomputer/logos-modules/releases/download/packages/medusa_core-0.4.0-linux-amd64.lgx), [medusa_ui](https://github.com/paradoxcomputer/logos-modules/releases/download/packages/medusa_ui-0.4.0-linux-amd64.lgx), [tip_jar](https://github.com/paradoxcomputer/logos-modules/releases/download/packages/tip_jar-0.2.1-linux-amd64.lgx) |
| macOS Apple silicon | [medusa_core](https://github.com/paradoxcomputer/logos-modules/releases/download/packages/medusa_core-0.4.0-darwin-arm64.lgx), [medusa_ui](https://github.com/paradoxcomputer/logos-modules/releases/download/packages/medusa_ui-0.4.0-darwin-arm64.lgx), [tip_jar](https://github.com/paradoxcomputer/logos-modules/releases/download/packages/tip_jar-0.2.1-darwin-arm64.lgx) |

Install `medusa_core` first — the other two depend on it.

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

Two ceilings apply, and both pull against carrying every variant in one file, since each extra
variant name means another full copy of the payload:

- GitHub refuses any file over **100 MB** in a repository. A larger payload goes on the
  `packages` release instead of into `lgx/`, described by a sidecar in `external/` carrying the
  url, size, sha256 and manifest. Git LFS is not an option: Pages serves the LFS pointer rather
  than the file. The sidecar holds everything `index.json` needs, so the index still
  regenerates on a clean checkout with no large file present.
- Basecamp gives up on a download after **300 seconds**. Not the 600 s `CURLOPT_TIMEOUT` in
  `package_downloader_lib.cpp` — the binding limit is `kDownloadIpcDeadlineMs = 5 * 60 * 1000`
  in Basecamp's `PackageCoordinator.cpp`, which wraps the whole batch, so curl's own cap never
  fires. There is no resume and no retry: a failed attempt deletes the partial file and the
  next one restarts at byte 0. At a measured ~200-240 kB/s that budget is roughly **60-70 MB
  for the entire batch**.

The batch matters because dependencies are not short-circuited. `PackageCoordinator` promotes
every dependency to a top-level entry and passes an empty installed-packages list
(`downloadResolvedDependenciesAsync(depsJson, QString(), ...)`), so a dependency is downloaded
in full even when that exact version is already installed, and discarded afterwards. Installing
the 0.2 MB `tip_jar` therefore transfers `medusa_core` as well.

And a catalog install can never fetch just one architecture: `index.json` holds a single `url`
per version, and `package_downloader` has no notion of platform at all — the architecture is
chosen later, by the package manager, from inside the `.lgx`.

So `medusa_core` cannot be delivered through the catalog on an ordinary connection. A measured
fetch of the 84 MB build took **373 s**, already past the deadline before any `-dev` twins are
added; with them it is 167 MB. It stays in `lgx/` under the plain names for fast connections,
and the per-architecture files on the `packages` release are the supported route — installed
from disk via **Install LGX Package**, where no download and therefore no deadline is involved.
Those files carry one architecture under both spellings, so they work on a portable build and a
build from source alike. `release-linux.yml` in the medusa repo publishes them next to the
merged package.

Making `medusa_core` small enough for the catalog means shrinking the payload: four Rust
binaries under `bin/` are 112 MB of the 128 MB variant, and stripping recovers only 15-24 %
because they are already close to stripped.

`zonescan_lite` has no dependencies and is 15 MB, ~180 s on the same link, so it installs from
the catalog comfortably. Note that carrying both variant spellings doubled it from 7.6 MB and
so halved its margin against the 300 s deadline; keep an eye on that if the app grows.
