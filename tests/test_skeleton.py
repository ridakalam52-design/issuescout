import json
import os
import tempfile
import unittest

from issuescout import cli, heuristics, report
from issuescout.github import GitHub
from issuescout.models import Issue, Report

RAW = [
    {"number": 3, "title": "App crashes on startup with traceback", "body": "Traceback ... KeyError", "html_url": "u3", "user": {"login": "a"}, "labels": []},
    {"number": 2, "title": "Add support for YAML config", "body": "Would be nice to allow YAML", "html_url": "u2", "user": {"login": "b"}, "labels": []},
    {"number": 9, "title": "a PR", "body": "", "html_url": "u9", "pull_request": {}},
    {"number": 1, "title": "App crashes on startup", "body": "same crash", "html_url": "u1", "user": {"login": "c"}, "labels": [{"name": "x"}]},
]


def fake_transport(calls):
    def t(method, url, data, headers):
        calls.append((method, url, data, headers))
        if method == "GET":
            return RAW if "page=1" in url else []
        return {}
    return t


class SkeletonTests(unittest.TestCase):
    def test_fetch_skips_prs_and_limits(self):
        calls = []
        issues = GitHub(token="", transport=fake_transport(calls)).fetch_open_issues("o/r", limit=2)
        self.assertEqual([i.number for i in issues], [3, 2])
        self.assertNotIn("Authorization", calls[0][3])

    def test_heuristics(self):
        issues = [Issue.from_github(r) for r in RAW if "pull_request" not in r]
        out = {t.issue.number: t for t in heuristics.triage_all(issues)}
        self.assertEqual(out[3].category, "bug")
        self.assertEqual(out[2].category, "feature")
        self.assertIn(1, [d.number for d in out[3].duplicates])

    def test_cli_dry_run_writes_reports_and_never_posts(self):
        calls = []
        with tempfile.TemporaryDirectory() as d:
            cli.run(["triage", "o/r", "--limit", "3", "--out", d, "--engine", "heuristic"], gh=GitHub(token="", transport=fake_transport(calls)))
            self.assertTrue(all(c[0] == "GET" for c in calls))
            data = json.load(open(os.path.join(d, "report.json")))
            self.assertEqual(len(data["issues"]), 3)
            self.assertIn("<html>", open(os.path.join(d, "report.html")).read())

    def test_apply_requires_token(self):
        with self.assertRaises(RuntimeError):
            GitHub(token="", transport=fake_transport([])).apply_triage("o/r", 1, ["bug"], "hi")

    def test_markdown_escapes_pipes(self):
        rep = Report("o/r", "now", "heuristic", heuristics.triage_all([Issue(1, "a|b", "", "u")]))
        self.assertIn("a\\|b", report.to_markdown(rep))


if __name__ == "__main__":
    unittest.main()
