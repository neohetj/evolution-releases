# Evolution Releases

Central release orchestration and immutable distribution metadata for Evolution binaries.
Component source remains in its owning private repository; binaries are GitHub Release assets,
never Git blobs.

## Published components

| Component | Source | Build target |
| --- | --- | --- |
| `operator` | `neohetj/operator` | `make release` |
| `keymaker-runner-step` | `neohetj/keymaker` | `make release-runner-step` |

Each component has an independent semantic version and release tag, such as
`operator-v1.4.2`. `runner-bundle-v<version>` freezes one compatible version of both components.
The reviewed `channels/runner-stable.json` file is the only mutable stable pointer.

## Release flow

1. Dispatch `Publish component` with a component, version, and exact 40-character source commit.
2. The workflow checks out that private commit, runs the source-owned cross-build, validates the
   component manifest, attests every output, and creates a new immutable component release.
3. Dispatch `Publish Runner bundle` with two already published component versions.
4. Dispatch `Promote Runner channel`; it opens a PR that copies the immutable bundle manifest to
   `channels/runner-stable.json`.

The repository secret `RELEASE_SOURCE_TOKEN` must be a fine-grained token or GitHub App token with
read-only Contents access to `neohetj/operator` and `neohetj/keymaker`. It receives no write access
to this repository; release creation uses this workflow's scoped `GITHUB_TOKEN`.

Enable GitHub immutable releases before the first production publication. Never use asset
overwrite flags or reuse a component or bundle version.

## Consumer URL

Keymaker should use the reviewed stable channel:

```text
https://raw.githubusercontent.com/neohetj/evolution-releases/main/channels/runner-stable.json
```

Production environments may instead pin the exact immutable bundle asset URL.

## Local validation

```bash
make check
python3 scripts/release_contract.py validate-component \
  --component operator /path/to/component-manifest.json
python3 scripts/release_contract.py validate-bundle /path/to/runner-bundle-manifest.json
```
