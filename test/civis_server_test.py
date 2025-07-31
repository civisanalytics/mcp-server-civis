import civis
import pytest
import json
import unittest.mock as mock
from mcp.shared.exceptions import McpError
from civis.tests import create_client_mock
import mcp_server_civis.server as civis_server
import asyncio

def basic_client_mock():
    """Create a basic civis client mock."""
    client = create_client_mock()
    client.default_database_credential_id = 1
    client.databases.list.return_value = [
        mock.Mock(id=5, name="test_db"),
        mock.Mock(id=6, name="another_db")
    ]
    return client

@mock.patch.object(civis_server, "civis")
def test_list_tools(m_civis):
    civis_mock = basic_client_mock()
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    tool_dict = {tool.name: tool for tool in server.tools()}

    # check a tool with required inputs
    assert tool_dict["get_table"].inputSchema['properties']['id']['type'] == 'number'
    assert tool_dict["get_table"].inputSchema['required'] == ["id"]

    # check a tool with array inputs
    list_input = tool_dict["list_tables"].inputSchema['properties']['table_tag_ids']
    assert list_input["type"] == "array"
    assert list_input["items"] == {"type": "number"}

@mock.patch.object(civis_server, "civis")
def test_get_user(m_civis):
    civis_mock = basic_client_mock()
    mock_user = {"id": 1, "name": "test_user"}
    civis_mock.users.list_me.return_value = mock_user
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.get_user()[0].text
    assert result == json.dumps(mock_user)

@mock.patch.object(civis_server, "civis")
def test_list_tables(m_civis):
    civis_mock = basic_client_mock()
    mock_tables = [{"id": 1, "name": "table1"}, {"id": 2, "name": "table2"}]
    civis_mock.tables.list.return_value = mock_tables
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
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

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
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

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.list_table_tags()[0].text
    assert result == json.dumps(mock_tags)
    civis_mock.table_tags.list.assert_called_once_with(iterator=True)

@mock.patch.object(civis_server, "civis")
def test_get_table(m_civis):
    civis_mock = basic_client_mock()
    mock_table = {"id": 123, "name": "test_table", "columns": []}
    civis_mock.tables.get.return_value = mock_table
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.get_table(id=123)[0].text
    assert result == json.dumps(mock_table)
    civis_mock.tables.get.assert_called_once_with(id=123)

@mock.patch.object(civis_server, "civis")
def test_run_query(m_civis):
    civis_mock = basic_client_mock()
    mock_query_result = mock.Mock()
    mock_query_result.result.return_value = {"data": [["row1"], ["row2"]], "columns": ["col1"]}
    m_civis.io.query_civis.return_value = mock_query_result
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
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

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.run_query(query="SELECT * FROM test", resultRows=5)[0].text
    expected_result = {"data": [["row1"]], "columns": ["col1"]}
    assert result == json.dumps(expected_result)
    m_civis.io.query_civis.assert_called_once_with(
        "SELECT * FROM test", 5, client=civis_mock, preview_rows=5
    )

@mock.patch.object(civis_server, "civis")
def test_list_workflows(m_civis):
    civis_mock = basic_client_mock()
    mock_workflows = [{"id": 1, "name": "workflow1"}, {"id": 2, "name": "workflow2"}]
    civis_mock.workflows.list.return_value = mock_workflows
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.list_workflows()[0].text
    assert result == json.dumps(mock_workflows)
    civis_mock.workflows.list.assert_called_once_with(author=None, limit=100)

@mock.patch.object(civis_server, "civis")
def test_list_workflows_with_user_id(m_civis):
    civis_mock = basic_client_mock()
    mock_workflows = [{"id": 1, "name": "workflow1"}]
    civis_mock.workflows.list.return_value = mock_workflows
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.list_workflows(user_id=123)[0].text
    assert result == json.dumps(mock_workflows)
    civis_mock.workflows.list.assert_called_once_with(author=[123], limit=100)

@mock.patch.object(civis_server, "civis")
def test_get_workflow(m_civis):
    civis_mock = basic_client_mock()
    mock_workflow = {"id": 123, "name": "test_workflow", "definition": "workflow: test"}
    civis_mock.workflows.get.return_value = mock_workflow
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.get_workflow(id=123)[0].text
    assert result == json.dumps(mock_workflow)
    civis_mock.workflows.get.assert_called_once_with(123)

@mock.patch.object(civis_server, "civis")
def test_list_workflow_executions(m_civis):
    civis_mock = basic_client_mock()
    mock_executions = [{"id": 1, "status": "success"}, {"id": 2, "status": "running"}]
    civis_mock.workflows.list_executions.return_value = mock_executions
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.list_workflow_executions(id=123)[0].text
    assert result == json.dumps(mock_executions)
    civis_mock.workflows.list_executions.assert_called_once_with(123)

@mock.patch.object(civis_server, "civis")
def test_create_workflow(m_civis):
    civis_mock = basic_client_mock()
    mock_workflow = {"id": 456, "name": "new_workflow", "definition": "workflow: new"}
    civis_mock.workflows.post.return_value = mock_workflow
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.create_workflow(name="new_workflow", definition="workflow: new")[0].text
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

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.create_workflow(
        name="new_workflow",
        definition="workflow: new",
        description="Test description"
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

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.create_workflow_execution(id=123)[0].text
    assert result == json.dumps(mock_execution)
    civis_mock.workflows.post_executions.assert_called_once_with(123)

@mock.patch.object(civis_server, "civis")
def test_list_jobs(m_civis):
    civis_mock = basic_client_mock()
    mock_jobs = [{"id": 1, "name": "job1"}, {"id": 2, "name": "job2"}]
    civis_mock.jobs.list.return_value = mock_jobs
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.list_jobs()[0].text
    assert result == json.dumps(mock_jobs)
    civis_mock.jobs.list.assert_called_once_with()

@mock.patch.object(civis_server, "civis")
def test_get_job(m_civis):
    civis_mock = basic_client_mock()
    mock_job = {"id": 123, "name": "test_job", "type": "sql"}
    civis_mock.jobs.get.return_value = mock_job
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.get_job(id=123)[0].text
    assert result == json.dumps(mock_job)
    civis_mock.jobs.get.assert_called_once_with(123)

@mock.patch.object(civis_server, "civis")
def test_run_job(m_civis):
    civis_mock = basic_client_mock()
    mock_run = {"id": 456, "job_id": 123, "status": "queued"}
    civis_mock.jobs.post_runs.return_value = mock_run
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.run_job(id=123)[0].text
    assert result == json.dumps(mock_run)
    civis_mock.jobs.post_runs.assert_called_once_with(123)

@mock.patch.object(civis_server, "civis")
def test_get_job_run(m_civis):
    civis_mock = basic_client_mock()
    mock_job_run = {"id": 456, "job_id": 123, "status": "success", "output": "completed"}
    civis_mock.jobs.get_runs.return_value = mock_job_run
    m_civis.APIClient.return_value = civis_mock

    server = civis_server.CivisServer(civis_mock, default_credential=3, default_database=5)
    result = server.get_job_run(job_id=123, run_id=456)[0].text
    assert result == json.dumps(mock_job_run)
    civis_mock.jobs.get_runs.assert_called_once_with(123, 456)