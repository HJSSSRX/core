import json

from cells.log_parser.plugin import (
    LogParserPlugin,
    run_parse_csv,
    run_parse_iis_log,
    run_parse_jsonl,
)


def test_plugin_registers_tools():
    plugin = LogParserPlugin()
    tools = plugin.register_tools()
    assert len(tools) == 4
    names = {t.name for t in tools}
    assert "parse_csv" in names
    assert "parse_jsonl" in names
    assert "parse_iis_log" in names


def test_parse_csv(tmp_path):
    f = tmp_path / "log.csv"
    f.write_text("timestamp,level,message\n2026-01-01,INFO,start\n2026-01-02,ERROR,fail\n")
    result = run_parse_csv(str(f))
    assert result["headers"] == ["timestamp", "level", "message"]
    assert result["row_count"] == 2
    assert result["rows"][0]["level"] == "INFO"


def test_parse_csv_tsv(tmp_path):
    f = tmp_path / "log.tsv"
    f.write_text("time\tsource\tmsg\nT1\tS1\tM1\nT2\tS2\tM2\n")
    result = run_parse_csv(str(f))
    assert result["delimiter"] == "tab"
    assert result["row_count"] == 2


def test_parse_csv_not_found():
    result = run_parse_csv("/nonexistent/file")
    assert "error" in result


def test_parse_jsonl(tmp_path):
    f = tmp_path / "events.jsonl"
    f.write_text(
        json.dumps({"event": "login", "user": "alice"}) + "\n"
        + json.dumps({"event": "logout", "user": "alice"}) + "\n"
    )
    result = run_parse_jsonl(str(f))
    assert result["row_count"] == 2
    assert result["keys"] == ["event", "user"]


def test_parse_jsonl_malformed(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"valid":1}\nnot json\n{"also":2}\n')
    result = run_parse_jsonl(str(f))
    assert result["row_count"] == 2
    assert result["parse_errors"] == 1


def test_parse_jsonl_not_found():
    result = run_parse_jsonl("/nonexistent/file")
    assert "error" in result


def test_parse_iis_log(tmp_path):
    f = tmp_path / "iis.log"
    f.write_text(
        "#Software: Microsoft IIS\n"
        "#Version: 1.0\n"
        "#Fields: date time cs-method cs-uri-stem sc-status\n"
        "2026-01-01 12:00:00 GET /index.html 200\n"
        "2026-01-01 12:01:00 POST /login 302\n"
    )
    result = run_parse_iis_log(str(f))
    assert result["fields"] == ["date", "time", "cs-method", "cs-uri-stem", "sc-status"]
    assert result["row_count"] == 2
    assert result["rows"][0]["cs-method"] == "GET"


def test_parse_iis_not_found():
    result = run_parse_iis_log("/nonexistent/file")
    assert "error" in result
