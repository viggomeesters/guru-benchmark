import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install-skill.sh"
CANONICAL = ROOT / "skills/guru-benchmark"
BRIDGE = ROOT / ".agents/skills/guru-benchmark/SKILL.md"


class SkillInstallTests(unittest.TestCase):
    def run_installer(self, *args, env=None):
        return subprocess.run(
            [str(INSTALLER), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_codex_bridge_delegates_to_canonical_skill(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("name: guru-benchmark", text)
        self.assertIn("../../../skills/guru-benchmark/SKILL.md", text)
        self.assertIn("only a discovery adapter", text)
        self.assertNotIn("Guru Score —", text)

    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            result = self.run_installer("--target", "hermes", "--destination-root", str(root), "--dry-run")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(f"destination={root / 'guru-benchmark'}", result.stdout)
            self.assertFalse(root.exists())

    def test_hermes_install_copies_complete_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "hermes-skills"
            result = self.run_installer("--target", "hermes", "--destination-root", str(root))
            self.assertEqual(0, result.returncode, result.stderr)
            installed = root / "guru-benchmark"
            source_files = sorted(path.relative_to(CANONICAL) for path in CANONICAL.rglob("*") if path.is_file())
            installed_files = sorted(path.relative_to(installed) for path in installed.rglob("*") if path.is_file())
            self.assertEqual(source_files, installed_files)
            self.assertTrue((installed / "references/contracts/manifest.json").is_file())

    def test_codex_default_uses_agents_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            env.pop("AGENTS_HOME", None)
            result = self.run_installer("--target", "codex", env=env)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((Path(tmp) / ".agents/skills/guru-benchmark/SKILL.md").is_file())
            self.assertFalse((Path(tmp) / ".codex/skills/guru-benchmark").exists())

    def test_existing_install_requires_force_and_force_keeps_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            first = self.run_installer("--target", "hermes", "--destination-root", str(root))
            self.assertEqual(0, first.returncode, first.stderr)
            marker = root / "guru-benchmark/local-marker.txt"
            marker.write_text("preserve me\n", encoding="utf-8")
            blocked = self.run_installer("--target", "hermes", "--destination-root", str(root))
            self.assertEqual(3, blocked.returncode)
            self.assertTrue(marker.is_file())
            replaced = self.run_installer("--target", "hermes", "--destination-root", str(root), "--force")
            self.assertEqual(0, replaced.returncode, replaced.stderr)
            backups = list(root.glob("guru-benchmark.backup.*"))
            self.assertEqual(1, len(backups))
            self.assertTrue((backups[0] / "local-marker.txt").is_file())
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
