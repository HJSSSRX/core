from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="ForHacker Dashboard", docs_url=None, redoc_url=None)

PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ForHacker Dashboard</title>
    <style>
        :root { --bg: #0d1117; --card: #161b22; --border: #30363d; --text: #c9d1d9; --accent: #58a6ff; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; max-width: 960px; margin: 0 auto; }
        h1 { color: var(--accent); }
    </style>
</head>
<body>
    <h1>ForHacker Dashboard</h1>
    <p style="color: #8b949e; margin-top: 2rem;">No active case. Run <code>forhacker case create &lt;name&gt;</code> to start.</p>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(PAGE_HTML)


@app.get("/case/{case_id}", response_class=HTMLResponse)
async def case_overview(case_id: str):
    return HTMLResponse(PAGE_HTML.replace("No active case", f"Case: {case_id}"))
