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


def test_parse_csv_no_headers(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("")
    result = run_parse_csv(str(f))
    assert "error" in result


def test_parse_csv_max_rows(tmp_path):
    f = tmp_path / "many.csv"
    lines = ["col1,col2"] + [f"a{i},b{i}" for i in range(10)]
    f.write_text("\n".join(lines))
    result = run_parse_csv(str(f), max_rows=3)
    assert result["row_count"] == 3


def test_parse_jsonl_empty_lines(tmp_path):
    f = tmp_path / "gap.jsonl"
    f.write_text('{"a":1}\n\n{"b":2}\n')
    result = run_parse_jsonl(str(f))
    assert result["row_count"] == 2


def test_parse_jsonl_max_rows(tmp_path):
    f = tmp_path / "big.jsonl"
    lines = [json.dumps({"n": i}) for i in range(10)]
    f.write_text("\n".join(lines))
    result = run_parse_jsonl(str(f), max_rows=3)
    assert result["row_count"] == 3


def test_parse_iis_log_max_rows(tmp_path):
    f = tmp_path / "many_iis.log"
    f.write_text(
        "#Fields: date time\n"
        + "\n".join(f"2026-01-0{i} 12:00:0{i}" for i in range(1, 8))
    )
    result = run_parse_iis_log(str(f), max_rows=3)
    assert result["row_count"] == 3


def test_parse_evtx_not_installed(tmp_path):
    from cells.log_parser.plugin import run_parse_evtx
    f = tmp_path / "test.evtx"
    f.write_text("dummy")
    result = run_parse_evtx(str(f))
    assert "python-evtx" in result.get("error", "")
