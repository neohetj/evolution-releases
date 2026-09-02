import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PUBLISH_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "publish-component.yml"


class PublishWorkflowTest(unittest.TestCase):
    def test_installs_source_declared_go_version_before_building(self) -> None:
        workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")

        source_checkout = workflow.index("          path: source")
        setup_go = workflow.index("      - name: Set up Go")
        component_build = workflow.index("      - name: Build component release")

        self.assertLess(source_checkout, setup_go)
        self.assertLess(setup_go, component_build)
        self.assertRegex(
            workflow,
            re.compile(
                r"uses: actions/setup-go@[0-9a-f]{40} # v\d+\n"
                r"        with:\n"
                r"          go-version-file: source/go\.mod\n"
                r"          cache-dependency-path: source/go\.sum"
            ),
        )


if __name__ == "__main__":
    unittest.main()
