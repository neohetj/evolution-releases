import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PUBLISH_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "publish-component.yml"


class PublishWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")

    def test_installs_source_declared_go_version_before_building(self) -> None:
        source_checkout = self.workflow.index("          path: source")
        setup_go = self.workflow.index("      - name: Set up Go")
        component_build = self.workflow.index("      - name: Build component release")

        self.assertLess(source_checkout, setup_go)
        self.assertLess(setup_go, component_build)
        self.assertRegex(
            self.workflow,
            re.compile(
                r"uses: actions/setup-go@[0-9a-f]{40} # v\d+\n"
                r"        with:\n"
                r"          go-version-file: source/go\.mod\n"
                r"          cache-dependency-path: source/go\.sum"
            ),
        )

    def test_checks_out_an_exact_matrix_dependency_before_building(self) -> None:
        self.assertIn("      matrix_commit:", self.workflow)
        self.assertIn(
            '[[ "${{ inputs.matrix_commit }}" =~ ^[0-9a-f]{40}$ ]]',
            self.workflow,
        )
        self.assertRegex(
            self.workflow,
            re.compile(
                r"- name: Check out exact private Matrix commit\n"
                r"        uses: actions/checkout@[0-9a-f]{40} # v\d+\n"
                r"        with:\n"
                r"          repository: neohetj/matrix\n"
                r"          ref: \$\{\{ inputs\.matrix_commit \}\}\n"
                r"          token: \$\{\{ env\.RELEASE_SOURCE_TOKEN \}\}\n"
                r"          path: matrix\n"
                r"          persist-credentials: false"
            ),
        )

        matrix_checkout = self.workflow.index(
            "      - name: Check out exact private Matrix commit"
        )
        matrix_dependency = self.workflow.index(
            "      - name: Prepare exact Matrix dependency"
        )
        component_build = self.workflow.index("      - name: Build component release")

        self.assertLess(matrix_checkout, matrix_dependency)
        self.assertLess(matrix_dependency, component_build)
        self.assertIn(
            'test "$(git -C matrix rev-parse HEAD)" = "${{ inputs.matrix_commit }}"',
            self.workflow,
        )
        self.assertIn(
            'go mod edit -replace="github.com/neohetj/matrix=$GITHUB_WORKSPACE/matrix"',
            self.workflow,
        )


if __name__ == "__main__":
    unittest.main()
