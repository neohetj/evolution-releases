# Release channels

`runner-stable.json` is created and updated only by the `Promote Runner Channel` workflow.
It is a reviewed copy of an immutable `runner-bundle-v<version>` manifest, so consumers can
use one stable HTTPS URL while every referenced binary remains pinned by version and SHA-256.
