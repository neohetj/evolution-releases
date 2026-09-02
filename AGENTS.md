# AGENTS.md

## Scope

This repository owns Evolution binary release orchestration, component manifests, compatibility
bundles, channel promotion, and release verification. It does not own component source code.

## Safety Boundaries

- Never commit binaries, credentials, local build output, or generated release assets.
- Build published binaries from an exact source repository and commit supplied to the workflow.
- Published component versions and bundle versions are immutable; never overwrite an asset.
- Every binary must have a lowercase SHA-256 digest and provenance metadata.
- Stable channel changes require review and may only reference an existing immutable bundle.
- Use least-privilege GitHub Actions permissions and pin third-party actions to immutable commits.

## Git And PR

- Use `main` as the long-lived branch and `codex/<type>/<topic>` for agent branches.
- Changes go through PR review; do not push feature work directly to `main`.
- Do not add AI co-author trailers.

## Validation

Run `make check` before handoff.
