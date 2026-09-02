import copy
import unittest

from scripts.release_contract import ContractError, compose_runner_bundle, validate_component_manifest


PLATFORMS = ("darwin-arm64", "darwin-amd64", "windows-amd64")


def component_manifest(component: str, version: str, repository: str) -> dict:
    artifacts = []
    for platform in PLATFORMS:
        goos, goarch = platform.split("-", 1)
        suffix = ".exe" if goos == "windows" else ""
        filename = f"{component}_{version}_{goos}_{goarch}{suffix}"
        artifacts.append(
            {
                "platform": platform,
                "os": goos,
                "arch": goarch,
                "filename": filename,
                "url": (
                    "https://github.com/neohetj/evolution-releases/releases/download/"
                    f"{component}-v{version}/{filename}"
                ),
                "sha256": "a" * 64,
            }
        )
    return {
        "schema_version": "2",
        "component": component,
        "version": version,
        "source": {"repository": repository, "commit": "1" * 40},
        "artifacts": artifacts,
    }


class ReleaseContractTest(unittest.TestCase):
    def test_composes_an_atomic_runner_bundle_for_every_supported_platform(self) -> None:
        operator = component_manifest("operator", "1.4.2", "neohetj/operator")
        runner_step = component_manifest(
            "keymaker-runner-step", "3.46.0", "neohetj/keymaker"
        )

        bundle = compose_runner_bundle("2026.9.0", operator, runner_step)

        self.assertEqual("2", bundle["schema_version"])
        self.assertEqual("runner", bundle["bundle"])
        self.assertEqual("2026.9.0", bundle["version"])
        self.assertEqual(operator, bundle["components"]["operator"])
        self.assertEqual(
            runner_step, bundle["components"]["keymaker-runner-step"]
        )

    def test_rejects_an_insecure_artifact_url(self) -> None:
        manifest = component_manifest("operator", "1.4.2", "neohetj/operator")
        manifest["artifacts"][0]["url"] = "http://downloads.example.test/operator"

        with self.assertRaisesRegex(ContractError, "HTTPS"):
            validate_component_manifest(manifest, expected_component="operator")

    def test_rejects_a_bundle_with_different_platform_sets(self) -> None:
        operator = component_manifest("operator", "1.4.2", "neohetj/operator")
        runner_step = component_manifest(
            "keymaker-runner-step", "3.46.0", "neohetj/keymaker"
        )
        runner_step = copy.deepcopy(runner_step)
        runner_step["artifacts"].pop()

        with self.assertRaisesRegex(ContractError, "platform set"):
            compose_runner_bundle("2026.9.0", operator, runner_step)

    def test_rejects_a_component_filename_that_does_not_match_its_identity(self) -> None:
        manifest = component_manifest(
            "keymaker-runner-step", "3.46.0", "neohetj/keymaker"
        )
        manifest["artifacts"][0]["filename"] = "operator_3.46.0_darwin_arm64"

        with self.assertRaisesRegex(ContractError, "filename"):
            validate_component_manifest(
                manifest, expected_component="keymaker-runner-step"
            )


if __name__ == "__main__":
    unittest.main()
