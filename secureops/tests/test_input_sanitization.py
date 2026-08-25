import pytest
from pydantic import ValidationError
from app.tools.schemas import SearchDocumentInput, DeleteDataInput, ReadDataInput


def test_path_traversal_in_tool_input_rejected():
    with pytest.raises(ValidationError) as exc:
        SearchDocumentInput(query="../../etc/passwd")
    assert "Path traversal sequence detected" in str(exc.value)


def test_path_traversal_windows_in_tool_input_rejected():
    with pytest.raises(ValidationError) as exc:
        ReadDataInput(target_resource="C:\\Windows\\System32\\cmd.exe")
    assert "Path traversal sequence detected" in str(exc.value)


def test_command_injection_pipe_rejected():
    with pytest.raises(ValidationError) as exc:
        DeleteDataInput(target_resource="users; rm -rf /", confirm_token="tok123")
    assert "Forbidden command injection characters detected" in str(exc.value)


def test_command_injection_backtick_rejected():
    with pytest.raises(ValidationError) as exc:
        SearchDocumentInput(query="`whoami`")
    assert "Forbidden command injection characters detected" in str(exc.value)


def test_extra_unknown_fields_in_tool_input_rejected():
    with pytest.raises(ValidationError) as exc:
        SearchDocumentInput(query="valid query", arbitrary_injected_field="malicious")
    assert "Extra inputs are not permitted" in str(exc.value)


def test_oversized_string_input_rejected():
    with pytest.raises(ValidationError) as exc:
        SearchDocumentInput(query="A" * 2000)
    assert "exceeds maximum allowed tool input limit" in str(exc.value)
