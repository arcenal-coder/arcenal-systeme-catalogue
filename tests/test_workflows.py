from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROMOTION_WORKFLOW = ROOT / ".github" / "workflows" / "promouvoir-diffusion.yml"


class PromotionWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = PROMOTION_WORKFLOW.read_text(encoding="utf-8")

    def test_promotion_can_dispatch_an_action(self) -> None:
        self.assertIn("actions: write", self.workflow)

    def test_promotion_dispatches_the_public_catalogue(self) -> None:
        self.assertIn("gh workflow run publier-catalogue.yml --ref main", self.workflow)

    def test_publication_is_dispatched_after_the_git_push(self) -> None:
        push_position = self.workflow.index("git push")
        dispatch_position = self.workflow.index("gh workflow run publier-catalogue.yml")

        self.assertLess(push_position, dispatch_position)


if __name__ == "__main__":
    unittest.main()
