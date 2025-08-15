import json
import civis
from typing import Sequence, Dict, Any, List, Callable
import sys
import mcp_server_civis

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class CivisServer:
    def __init__(self, client, default_credential, default_database):
        self.client = client
        self.default_credential = default_credential
        self.default_database = default_database

    @staticmethod
    def register_tool(input_schema: Dict[str, Any]):
        """
        Decorator that sets the input_schema as an attribute on the function.
        This is later used by the .tools method to generate the tool list.

        Args:
            input_schema: The input schema properties for the tool
        """

        def decorator(func: Callable):
            setattr(func, "__input_schema__", input_schema)
            setattr(func, "tool", True)
            return func

        return decorator

    def tools(self) -> List[Tool]:
        """Generates a list of available tools based on registered methods,
        their docstrings, and the input schema."""
        tool_list = []

        for name in dir(self):
            attr = getattr(self, name)
            if callable(attr) and hasattr(attr, "tool"):
                input_schema = getattr(attr, "__input_schema__", {})
                tool = Tool(
                    name=name, description=attr.__doc__, inputSchema=input_schema
                )
                tool_list.append(tool)
        return tool_list

    def list_result(self, result, last_cursor=None):
        parsed_result = [r.json() if hasattr(r, "json") else r for r in result]
        if last_cursor is None:
            return [TextContent(type="text", text=json.dumps(parsed_result))]
        next_cursor = last_cursor + 1
        if not parsed_result:
            next_cursor = None
        paginated_result = {"results": parsed_result, "nextCursor": next_cursor}
        return [TextContent(type="text", text=json.dumps(paginated_result))]

    def single_result(self, result):
        parsed_result = result.json() if hasattr(result, "json") else result
        return [TextContent(type="text", text=json.dumps(parsed_result))]

    # --- User tools ---
    @register_tool(input_schema={"type": "object", "properties": {}})
    def get_user(self):
        """Get my civis user information"""
        return self.single_result(self.client.users.list_me())

    # --- Table and query tools ---
    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "schema": {"type": "string", "description": "Schema name"},
                "table_tag_ids": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "a list of table tags IDs to filter by",
                },
            },
        }
    )
    def list_tables(self, schema=None, table_tag_ids=None):
        """Get the tables in a database"""
        # Use the server schema if provided, otherwise use the parameter
        return self.list_result(
            self.client.tables.list(
                schema=schema,
                database_id=self.default_database,
                table_tag_ids=table_tag_ids,
                iterator=True,
            )
        )

    @register_tool(input_schema={"type": "object", "properties": {}})
    def list_table_tags(self):
        """Get the list of possible table tags for a database"""
        return self.list_result(self.client.table_tags.list(iterator=True))

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "id": {"type": "number", "description": "The unique numeric table ID"}
            },
            "required": ["id"],
        }
    )
    def get_table(self, id):
        """Get information about a specific table including columns, sample rows,
        and how recently the table was updated."""
        return self.single_result(self.client.tables.get(id=id))

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query to execute"},
                "resultRows": {
                    "type": "number",
                    "description": """
                        The maximum number of rows to return from the query.
                        Must be <=1000.
                        """,
                    "default": 10,
                },
            },
            "required": ["query"],
        }
    )
    def run_query(self, query, resultRows=10):
        """Run a query with the user's default credentials and database. The maximum
        value of resultRows is 1000, so is best for small tables, aggregates or samples."""
        return self.single_result(
            civis.io.query_civis(
                query,
                self.default_database,
                client=self.client,
                preview_rows=resultRows,
            ).result()
        )

    # --- Workflow tools ---
    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Optional user ID to filter Workflows",
                },
                "cursor": {
                    "type": "integer",
                    "description": "Page number for pagination (default: 1)",
                    "default": 1,
                    "minimum": 1,
                },
            },
        }
    )
    def list_workflows(self, user_id=None, cursor=1):
        """Get recent Workflows"""
        user_ids = [user_id] if user_id else None
        return self.list_result(
            self.client.workflows.list(author=user_ids, page_num=cursor),
            cursor,
        )

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "Workflow ID"}},
            "required": ["id"],
        }
    )
    def get_workflow(self, id):
        """Get a specific Workflow by ID"""
        return self.single_result(self.client.workflows.get(id))

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "Workflow ID to get executions for",
                },
                "cursor": {
                    "type": "integer",
                    "description": "Page number for pagination (default: 1)",
                    "default": 1,
                    "minimum": 1,
                },
            },
            "required": ["id"],
        }
    )
    def list_workflow_executions(self, id, cursor=1):
        """Get recent Workflow executions"""
        return self.list_result(
            self.client.workflows.list_executions(id, page_num=cursor), cursor
        )

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the new Workflow",
                },
                "description": {
                    "type": "string",
                    "description": "A description of the new Workflow",
                },
                "definition": {
                    "type": "string",
                    "description": "Workflow YAML matching the OpenStack Mistral DSL",
                },
            },
            "required": ["name", "definition"],
        }
    )
    def create_workflow(self, name, definition=None, description=None):
        """Create a new Workflow"""
        return self.single_result(
            self.client.workflows.post(
                name=name, definition=definition, description=description
            )
        )

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "number",
                    "description": "The ID of the Workflow to execute",
                }
            },
            "required": ["id"],
        }
    )
    def create_workflow_execution(self, id):
        """Execute a Workflow"""
        return self.single_result(self.client.workflows.post_executions(id))

    # --- Job tools ---
    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": """
                        The types of jobs to list. Specify multiple values as a
                        comma-separated list (e.g., `A,B`).
                        Valid job types include: JobTypes::Query, JobTypes::SqlRunner,
                        JobTypes::CsvImport, JobTypes::Import,
                        JobTypes::ContainerDocker, JobTypes::AutoImport,
                        JobTypes::Dbsync, JobTypes::PythonDocker, JobTypes::ScriptedSql,
                        JobTypes::GdocExport, JobTypes::GdocImport,
                        JobTypes::CsvExport, JobTypes::CassNcoa, JobTypes::RDocker,
                        JobTypes::DbtDocker, JobTypes::Geocode,
                        JobTypes::IdentityResolution
                      """,
                },
                "cursor": {
                    "type": "integer",
                    "description": "Page number for pagination (default: 1)",
                    "default": 1,
                    "minimum": 1,
                },
            },
        }
    )
    def list_jobs(self, type=None, cursor=1):
        """Get recent Jobs"""
        return self.list_result(
            self.client.jobs.list(
                type=type,
                page_num=cursor,
            ),
            cursor,
        )

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "Job ID"}},
            "required": ["id"],
        }
    )
    def get_job(self, id):
        """Get the details of a specific Job by ID"""
        return self.single_result(self.client.jobs.get(id))

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "Job ID"}},
            "required": ["id"],
        }
    )
    def run_job(self, id):
        """Create a Job run"""
        return self.single_result(self.client.jobs.post_runs(id))

    @register_tool(
        input_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Job ID"},
                "run_id": {"type": "integer", "description": "Run ID"},
            },
            "required": ["job_id", "run_id"],
        }
    )
    def get_job_run(self, job_id, run_id):
        """Get the details for a specific run of a Job"""
        return self.single_result(self.client.jobs.get_runs(job_id, run_id))


async def serve(api_key: str | None):
    server_name = "mcp-civis"

    server = Server(server_name)
    client = civis.APIClient(
        api_key=api_key, user_agent=f"mcp-server-civis ({mcp_server_civis.__version__})"
    )

    default_credential = client.default_database_credential_id
    default_database = sorted([d.id for d in client.databases.list()])[0]

    civis_server = CivisServer(client, default_credential, default_database)

    # TODO: Convert operations without side effects to resources
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available civis tools."""
        return civis_server.tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
        """Handle tool calls for civis queries."""
        try:
            return getattr(civis_server, name)(**arguments)

        except Exception as e:
            print(f"Error processing mcp-server-civis query: {e}", file=sys.stderr)
            raise ValueError(f"Error processing mcp-server-civis query: {e}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
