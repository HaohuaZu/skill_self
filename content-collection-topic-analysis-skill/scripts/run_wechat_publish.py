#!/usr/bin/env python3
"""Entry point for Feishu-to-WeChat publishing."""

from content_collection_topic_analysis.publish_cli import run_from_args


def main() -> int:
    return run_from_args()


if __name__ == "__main__":
    raise SystemExit(main())
