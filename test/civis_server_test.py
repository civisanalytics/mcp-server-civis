import pytest
import json
import unittest.mock as mock
from civis.tests import create_client_mock
import mcp_server_civis.server as civis_server


def basic_client_mock():
    """Create a basic civis client mock."""
    client = create_client_mock()
    client.default_database_credential_id = 1
    client.databases.list.return_value = [
        mock.Mock(id=5, name="test_db"),
        mock.Mock(id=6, name="another_db"),
    ]
    return client


def default_server(civis_mock):
    return civis_server.CivisServer(
        civis_mock,
        default_credential=3,
        default_database=5,
        schema=None,
        description=None,
    )


@mock.patch.object(civis_server, "civis")
def test_list_tools(m_civis):
    civis_mock = basic_client_mock()
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    tool_dict = {tool.name: tool for tool in server.tools()}

    # check a tool with required inputs
    assert tool_dict["get_table"].inputSchema["properties"]["id"]["type"] == "number"
    assert tool_dict["get_table"].inputSchema["required"] == ["id"]

    # check a tool with array inputs
    list_input = tool_dict["list_tables"].inputSchema["properties"]["table_tag_ids"]
    assert list_input["type"] == "array"
    assert list_input["items"] == {"type": "number"}


@mock.patch.object(civis_server, "civis")
def test_list_tools_with_schema_filter(m_civis):
    civis_mock = basic_client_mock()
    m_civis.APIClient.return_value = civis_mock

    # Create server with schema to enable filtering
    server = civis_server.CivisServer(
        civis_mock,
        default_credential=3,
        default_database=5,
        schema="test_schema",
        description=None,
    )

    tools = server.tools()
    tool_names = {tool.name for tool in tools}

    # When schema is provided, only these 4 tools should be available
    expected_tools = {
        "run_query",
        "list_tables",
        "get_table",
        "pull_data_list",
        "publish_html_report"
        }

    assert len(tools) == 5
    assert tool_names == expected_tools

    # Verify that other tools are filtered out
    assert "get_user" not in tool_names
    assert "list_workflows" not in tool_names
    assert "list_jobs" not in tool_names


@mock.patch.object(civis_server, "civis")
def test_get_user(m_civis):
    civis_mock = basic_client_mock()
    mock_user = {"id": 1, "name": "test_user"}
    civis_mock.users.list_me.return_value = mock_user
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.get_user()[0].text
    assert result == json.dumps(mock_user)


@mock.patch.object(civis_server, "civis")
def test_list_tables(m_civis):
    civis_mock = basic_client_mock()
    mock_tables = [{"id": 1, "name": "table1"}, {"id": 2, "name": "table2"}]
    civis_mock.tables.list.return_value = mock_tables
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.list_tables()[0].text
    assert result == json.dumps(mock_tables)
    civis_mock.tables.list.assert_called_once_with(
        schema=None, database_id=5, table_tag_ids=None, iterator=True
    )


@mock.patch.object(civis_server, "civis")
def test_list_tables_with_params(m_civis):
    civis_mock = basic_client_mock()
    mock_tables = [{"id": 1, "name": "table1"}]
    civis_mock.tables.list.return_value = mock_tables
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.list_tables(schema="test_schema", table_tag_ids=[1, 2])[0].text
    assert result == json.dumps(mock_tables)
    civis_mock.tables.list.assert_called_once_with(
        schema="test_schema", database_id=5, table_tag_ids=[1, 2], iterator=True
    )


@mock.patch.object(civis_server, "civis")
def test_list_table_tags(m_civis):
    civis_mock = basic_client_mock()
    mock_tags = [{"id": 1, "name": "tag1"}, {"id": 2, "name": "tag2"}]
    civis_mock.table_tags.list.return_value = mock_tags
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.list_table_tags()[0].text
    assert result == json.dumps(mock_tags)
    civis_mock.table_tags.list.assert_called_once_with(iterator=True)


@mock.patch.object(civis_server, "civis")
def test_get_table(m_civis):
    civis_mock = basic_client_mock()
    mock_table = {"id": 123, "name": "test_table", "columns": []}
    civis_mock.tables.get.return_value = mock_table
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.get_table(id=123)[0].text
    assert result == json.dumps(mock_table)
    civis_mock.tables.get.assert_called_once_with(id=123)


@mock.patch.object(civis_server, "civis")
def test_run_query(m_civis):
    civis_mock = basic_client_mock()
    mock_query_result = mock.Mock()
    mock_query_result.result.return_value = {
        "data": [["row1"], ["row2"]],
        "columns": ["col1"],
    }
    m_civis.io.query_civis.return_value = mock_query_result
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.run_query(query="SELECT * FROM test")[0].text
    expected_result = {"data": [["row1"], ["row2"]], "columns": ["col1"]}
    assert result == json.dumps(expected_result)
    m_civis.io.query_civis.assert_called_once_with(
        "SELECT * FROM test", 5, client=civis_mock, preview_rows=10
    )


@mock.patch.object(civis_server, "civis")
def test_run_query_with_result_rows(m_civis):
    civis_mock = basic_client_mock()
    mock_query_result = mock.Mock()
    mock_query_result.result.return_value = {"data": [["row1"]], "columns": ["col1"]}
    m_civis.io.query_civis.return_value = mock_query_result
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.run_query(query="SELECT * FROM test", resultRows=5)[0].text
    expected_result = {"data": [["row1"]], "columns": ["col1"]}
    assert result == json.dumps(expected_result)
    m_civis.io.query_civis.assert_called_once_with(
        "SELECT * FROM test", 5, client=civis_mock, preview_rows=5
    )


@mock.patch.object(civis_server, "civis")
def test_pull_data_list(m_civis):
    civis_mock = basic_client_mock()
    mock_export_result = mock.Mock()
    mock_export_result.result.return_value = {
        "output": [
            {"path": "https://example.com/download1.csv"},
            {"path": "https://example.com/download2.csv"}
        ]
    }
    m_civis.io.export_to_civis_file.return_value = mock_export_result
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.pull_data_list(query="SELECT * FROM large_table")[0].text
    expected_result = {
        "urls": [
            "https://example.com/download1.csv",
            "https://example.com/download2.csv"
            ]
    }
    assert result == json.dumps(expected_result)
    m_civis.io.export_to_civis_file.assert_called_once_with(
        "SELECT * FROM large_table",
        5,
        job_name="MCP Export",
        client=civis_mock,
        hidden=True,
    )


@mock.patch.object(civis_server, "civis")
def test_list_workflows(m_civis):
    civis_mock = basic_client_mock()
    mock_workflows = [{"id": 1, "name": "workflow1"}, {"id": 2, "name": "workflow2"}]
    expected_result = {
        "results": mock_workflows,
        "nextCursor": 2,
    }

    civis_mock.workflows.list.return_value = mock_workflows
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.list_workflows()[0].text
    assert result == json.dumps(expected_result)
    civis_mock.workflows.list.assert_called_once_with(author=None, page_num=1)


@mock.patch.object(civis_server, "civis")
def test_list_workflows_with_user_id(m_civis):
    civis_mock = basic_client_mock()
    mock_workflows = [{"id": 1, "name": "workflow1"}]
    expected_result = {"results": mock_workflows, "nextCursor": 2}
    civis_mock.workflows.list.return_value = mock_workflows
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.list_workflows(user_id=123)[0].text
    assert result == json.dumps(expected_result)
    civis_mock.workflows.list.assert_called_once_with(author=[123], page_num=1)


@mock.patch.object(civis_server, "civis")
def test_get_workflow(m_civis):
    civis_mock = basic_client_mock()
    mock_workflow = {"id": 123, "name": "test_workflow", "definition": "workflow: test"}
    civis_mock.workflows.get.return_value = mock_workflow
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.get_workflow(id=123)[0].text
    assert result == json.dumps(mock_workflow)
    civis_mock.workflows.get.assert_called_once_with(123)


@mock.patch.object(civis_server, "civis")
def test_list_workflow_executions(m_civis):
    civis_mock = basic_client_mock()
    mock_executions = [{"id": 1, "status": "success"}, {"id": 2, "status": "running"}]
    expected_result = {
        "results": mock_executions,
        "nextCursor": 2,
    }
    civis_mock.workflows.list_executions.return_value = mock_executions
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.list_workflow_executions(id=123)[0].text
    assert result == json.dumps(expected_result)
    civis_mock.workflows.list_executions.assert_called_once_with(123, page_num=1)


@mock.patch.object(civis_server, "civis")
def test_create_workflow(m_civis):
    civis_mock = basic_client_mock()
    mock_workflow = {"id": 456, "name": "new_workflow", "definition": "workflow: new"}
    civis_mock.workflows.post.return_value = mock_workflow
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.create_workflow(name="new_workflow", definition="workflow: new")[
        0
    ].text
    assert result == json.dumps(mock_workflow)
    civis_mock.workflows.post.assert_called_once_with(
        name="new_workflow", definition="workflow: new", description=None
    )


@mock.patch.object(civis_server, "civis")
def test_create_workflow_with_description(m_civis):
    civis_mock = basic_client_mock()
    mock_workflow = {"id": 456, "name": "new_workflow", "definition": "workflow: new"}
    civis_mock.workflows.post.return_value = mock_workflow
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.create_workflow(
        name="new_workflow", definition="workflow: new", description="Test description"
    )[0].text
    assert result == json.dumps(mock_workflow)
    civis_mock.workflows.post.assert_called_once_with(
        name="new_workflow", definition="workflow: new", description="Test description"
    )


@mock.patch.object(civis_server, "civis")
def test_create_workflow_execution(m_civis):
    civis_mock = basic_client_mock()
    mock_execution = {"id": 789, "workflow_id": 123, "status": "queued"}
    civis_mock.workflows.post_executions.return_value = mock_execution
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.create_workflow_execution(id=123)[0].text
    assert result == json.dumps(mock_execution)
    civis_mock.workflows.post_executions.assert_called_once_with(123)


@mock.patch.object(civis_server, "civis")
def test_list_jobs(m_civis):
    civis_mock = basic_client_mock()
    mock_jobs = [{"id": 1, "name": "job1"}, {"id": 2, "name": "job2"}]
    expected_result = {
        "results": mock_jobs,
        "nextCursor": 2,
    }
    civis_mock.jobs.list.return_value = mock_jobs
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.list_jobs()[0].text
    assert result == json.dumps(expected_result)
    civis_mock.jobs.list.assert_called_once_with(type=None, page_num=1)


@mock.patch.object(civis_server, "civis")
def test_get_job(m_civis):
    civis_mock = basic_client_mock()
    mock_job = {"id": 123, "name": "test_job", "type": "sql"}
    civis_mock.jobs.get.return_value = mock_job
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.get_job(id=123)[0].text
    assert result == json.dumps(mock_job)
    civis_mock.jobs.get.assert_called_once_with(123)


@mock.patch.object(civis_server, "civis")
def test_run_job(m_civis):
    civis_mock = basic_client_mock()
    mock_run = {"id": 456, "job_id": 123, "status": "queued"}
    civis_mock.jobs.post_runs.return_value = mock_run
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.run_job(id=123)[0].text
    assert result == json.dumps(mock_run)
    civis_mock.jobs.post_runs.assert_called_once_with(123)


@mock.patch.object(civis_server, "civis")
def test_get_job_run(m_civis):
    civis_mock = basic_client_mock()
    mock_job_run = {
        "id": 456,
        "job_id": 123,
        "status": "success",
        "output": "completed",
    }
    civis_mock.jobs.get_runs.return_value = mock_job_run
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.get_job_run(job_id=123, run_id=456)[0].text
    assert result == json.dumps(mock_job_run)
    civis_mock.jobs.get_runs.assert_called_once_with(123, 456)


@mock.patch.object(civis_server, "civis")
def test_publish_html_report(m_civis):
    civis_mock = basic_client_mock()
    mock_report_result = {
        "id": 123,
        "name": "Test Report",
        "description": "A test report",
        "code_body": "<html><body>Hello World</body></html>"
    }
    civis_mock.reports.post.return_value = mock_report_result
    m_civis.APIClient.return_value = civis_mock

    server = default_server(civis_mock)
    result = server.publish_html_report(
        body="<html><body>Hello World</body></html>",
        name="Test Report",
        description="A test report"
    )[0].text

    expected_result = {
        'url': "https://platform.civisanalytics.com/spa/#/reports/123?fullscreen=true"
    }

    assert result == json.dumps(expected_result)
    civis_mock.reports.post.assert_called_once_with(
        name="Test Report",
        code_body="<html><body>Hello World</body></html>",
        description="A test report"
    )


@mock.patch.object(civis_server, "civis")
def test_run_query_with_schema_adds_readonly_transaction(m_civis):
    civis_mock = basic_client_mock()
    mock_query_result = mock.Mock()
    mock_query_result.result.return_value = {
        "data": [["row1"]],
        "columns": ["col1"],
    }
    m_civis.io.query_civis.return_value = mock_query_result
    m_civis.APIClient.return_value = civis_mock

    # Create server with schema
    server = civis_server.CivisServer(
        civis_mock,
        default_credential=3,
        default_database=5,
        schema="test_schema",
        description=None,
    )

    server.run_query(query="SELECT * FROM test_schema.test_table")

    # Verify that the query was wrapped in BEGIN READ ONLY
    m_civis.io.query_civis.assert_called_once_with(
        "BEGIN READ ONLY; SELECT * FROM test_schema.test_table",
        5,
        client=civis_mock,
        preview_rows=10
    )


@mock.patch.object(civis_server, "civis")
def test_pull_data_list_with_schema_adds_readonly_transaction(m_civis):
    civis_mock = basic_client_mock()
    mock_export_result = mock.Mock()
    mock_export_result.result.return_value = {
        "output": [
            {"path": "https://example.com/file1.csv"},
            {"path": "https://example.com/file2.csv"}
        ]
    }
    m_civis.io.export_to_civis_file.return_value = mock_export_result
    m_civis.APIClient.return_value = civis_mock

    # Create server with schema
    server = civis_server.CivisServer(
        civis_mock,
        default_credential=3,
        default_database=5,
        schema="test_schema",
        description=None,
    )

    server.pull_data_list(query="SELECT * FROM test_schema.large_table")

    # Verify that the query was wrapped in BEGIN READ ONLY
    m_civis.io.export_to_civis_file.assert_called_once_with(
        "BEGIN READ ONLY; SELECT * FROM test_schema.large_table",
        5,
        job_name="MCP Export",
        client=civis_mock,
        hidden=True
    )


@mock.patch.object(civis_server, "civis")
def test_run_query_with_schema_validates_schema_in_query(m_civis):
    civis_mock = basic_client_mock()
    m_civis.APIClient.return_value = civis_mock

    # Create server with schema
    server = civis_server.CivisServer(
        civis_mock,
        default_credential=3,
        default_database=5,
        schema="test_schema",
        description=None,
    )

    # Test that query without schema raises ValueError
    with pytest.raises(ValueError, match="Specified schema was not in query"):
        server.run_query(query="SELECT * FROM other_schema.test_table")

    # Verify that query_civis was never called
    m_civis.io.query_civis.assert_not_called()


@mock.patch.object(civis_server, "civis")
def test_pull_data_list_with_schema_validates_schema_in_query(m_civis):
    civis_mock = basic_client_mock()
    m_civis.APIClient.return_value = civis_mock

    # Create server with schema
    server = civis_server.CivisServer(
        civis_mock,
        default_credential=3,
        default_database=5,
        schema="test_schema",
        description=None,
    )

    # Test that query without schema raises ValueError
    with pytest.raises(ValueError, match="Specified schema was not in query"):
        server.pull_data_list(query="SELECT * FROM other_schema.large_table")

    # Verify that export_to_civis_file was never called
    m_civis.io.export_to_civis_file.assert_not_called()
