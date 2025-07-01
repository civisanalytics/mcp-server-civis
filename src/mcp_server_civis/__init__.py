from .server import serve
import os


def main():
    """Civis MCP Server - MCP capability for interacting with the civis platform"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to interact with civis platform"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Override Civis API key",
        default=os.getenv("CIVIS_API_KEY"),
    )

    args = parser.parse_args()
    asyncio.run(serve(args.api_key))


if __name__ == "__main__":
    main()
