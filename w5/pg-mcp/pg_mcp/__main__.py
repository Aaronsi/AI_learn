"""Main entry point for pg-mcp"""

import sys

from pg_mcp.server import mcp


def main() -> None:
    """主入口"""
    # FastMCP自动处理stdio/SSE传输
    mcp.run()


if __name__ == "__main__":
    main()

