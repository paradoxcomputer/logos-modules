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

`medusa_core` is why this is written down. It is 84 MB with one set of variant names and 167 MB
with both. A measured fetch of the 84 MB build took **373 s** — already past the 300 s deadline
on an ordinary connection, before any `-dev` twins are added. It therefore ships with the plain
names only; doubling it would not have made it installable, only slower. Nothing that depends
on it (`medusa_ui`, `tip_jar`) can be installed from this catalog on such a link either, and
the failure is silent: when the deadline fires the transport hands back an empty result, which
`PackageCoordinator` cannot tell apart from "nothing to install", so the dialog reports success
and offers Launch while nothing was installed.

The fix is to make `medusa_core` smaller — four Rust binaries under `bin/` are 112 MB of the
128 MB variant. Stripping recovers only 15-24 %; they are already close to stripped.

`zonescan_lite` has no dependencies and is 15 MB, ~180 s on the same link, so it installs
comfortably. Note that carrying both variant spellings doubled it from 7.6 MB and so halved its
margin against the 300 s deadline; keep an eye on that if the app grows.
