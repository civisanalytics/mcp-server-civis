# Civis MCP Server

A Model Context Protocol server that provides an interface to the Civis Platform

## Configuration

### Configure for Claude.app

Add to your Claude settings:

<details>
<summary>Using docker</summary>

```json
{
  "mcpServers": {
    "civis": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "civis/mcp-server"]
    }
  }
}
```
</details>

### Configure for VS Code

Add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)`.

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace. This will allow you to share the configuration with others.

> Note that the `mcp` key is needed when using the `mcp.json` file.

<details>
<summary>Using Docker</summary>

```json
{
  "mcp": {
    "inputs": [{
      "type": "promptString",
      "id": "CIVIS_API_KEY",
      "description": "CIVIS API Key",
      "password": true
    }],
    "servers": {
      "civis": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e", "CIVIS_API_KEY",
          "civis/mcp-server",
      ],
      "env": {
          "CIVIS_API_KEY": "${input:CIVIS_API_KEY}"
      }
    }
  }
}
```
</details>

## Examples of Questions

1. "Query the donations table from the donors schema in Civis. How many donations happened in the last 30 days compared to one year ago?"
2. "Add all the tables from the salesforce_prod schema in Civis as dbt sources. Include column names and types."
3. "Post this YAML file as a Civis workflow and execute it."
4. "How long did my most recent workflow take to execute?"

## Local Installation

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *mcp-server-civis*.

### Using PIP

Alternatively you can install `mcp-server-civis` via pip:

```bash
pip install mcp-server-civis
```

After installation, you can run it as a script using:

```bash
python -m mcp_server_civis
```

## Debugging

You can use the MCP inspector to debug the server. For uvx installations:

```bash
npx @modelcontextprotocol/inspector uvx mcp-server-civis
```

Or if you've installed the package in a specific directory or are developing on it:

```bash
cd path/to/servers/src/time
npx @modelcontextprotocol/inspector uv run mcp-server-civis
```

## Build

Docker build:

```bash
docker build -t civisanalytics/mcp-server .
```

## Contributing

We encourage contributions to help expand and improve mcp-server-civis. Whether you want to add new time-related tools, enhance existing functionality, or improve documentation, your input is valuable.

For examples of other MCP servers and implementation patterns, see:
https://github.com/modelcontextprotocol/servers

Pull requests are welcome! Feel free to contribute new ideas, bug fixes, or enhancements to make mcp-server-civis even more powerful and useful.

## License

mcp-server-civis is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
