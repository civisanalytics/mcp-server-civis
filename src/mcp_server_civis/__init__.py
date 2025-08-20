from .server import serve
from importlib.metadata import version
import os

__version__ = version("mcp_server_civis")


def main():
    """Civis MCP Server - MCP capability for interacting with the Civis Platform"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to interact with Civis Platform"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Override Civis API key",
        default=os.getenv("CIVIS_API_KEY"),
    )
    parser.add_argument(
        "--schema",
        type=str,
        help="""Limit data tools to a specific database schema.
                Non-data tools will be disabled.""",
        default=None,
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Custom description for data in Civis",
        default=None,
    )
    args = parser.parse_args()
    asyncio.run(serve(args.api_key, args.schema, args.description))


if __name__ == "__main__":
    main()
