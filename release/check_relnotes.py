"""Short helper script to check that a PR has exactly one relnotes label."""

import json
import os
import sys

if __name__ == "__main__":
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path is None:
        raise RuntimeError("Can only check changelog on github actions")

    with open(event_path) as event_file:
        event = json.load(event_file)

    labels = [
        label["name"]
        for label in event["pull_request"]["labels"]
        if label["name"].startswith("relnotes-") or label["name"] == "documentation"
    ]

    if not labels:
        print(
            "No suitable label found, please add either one of the `relnotes-` or `documentation` labels.",
            file=sys.stderr,
        )
        exit(1)

    if len(labels) > 1:
        print(f'Multiple relnotes labels found: `{"`, `".join(labels)}`', file=sys.stderr)
        exit(1)

    print("Found suitable label:", labels[0])
    exit(0)
