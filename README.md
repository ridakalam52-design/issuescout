# IssueScout

An open-source GitHub issue-triage helper. Point it at a repo and it fetches the newest open
issues, classifies them, suggests labels and priority, flags likely duplicates and drafts a reply.
Output is a Markdown, JSON and static HTML report. It is a dry run by default.

```bash
pip install -e .
issuescout triage owner/repo --limit 5
python -m unittest discover tests
```

This first version is rule-based only (no models).
