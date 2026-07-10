# Composio App Research Agent

Automated research of 100 apps across 10 categories — authentication methods, API surface, self-serve access, MCP server availability, and buildability verdicts for Composio's agent toolkit platform.

**[View Live Report →](https://krvatsal.github.io/composio-task/site/)**

## What It Does

For each of the 100 assigned apps, the agent:
1. **Searches** for API documentation, pricing pages, and MCP servers using Tavily
2. **Extracts** structured data via Azure GPT-4o-mini with function calling
3. **Cross-references** with Composio SDK to identify which apps are already supported
4. **Validates** evidence URLs via HTTP HEAD requests
5. **Analyzes** cross-cutting patterns (auth distribution, self-serve rates, buildability blockers)
6. **Generates** a self-contained HTML report with interactive table, charts, and actionable insights

## Key Findings

| Metric | Value |
|--------|-------|
| Apps Researched | 100 |
| Ready to Build | 75 |
| Self-Serve Access | 89% |
| Already in Composio | 57 |
| Untapped Ready Apps | 18 |
| Evidence URLs Valid | 93% |

## Project Structure

```
├── agent/
│   ├── app_list.py          # 100 apps organized by category
│   ├── schemas.py           # Pydantic models + tool schema for structured output
│   ├── researcher.py        # Core: Tavily search + Azure GPT-4o-mini extraction
│   ├── orchestrator.py      # Runs researcher across 100 apps with resume/retry
│   ├── verifier.py          # URL validation + spot-check framework
│   ├── patterns.py          # Pattern extraction from research data
│   ├── composio_check.py    # Composio SDK cross-reference
│   └── export.py            # Generates self-contained HTML deliverable
├── data/
│   ├── research_pass1.json  # Raw research output (100 apps)
│   ├── patterns.json        # Extracted patterns
│   └── verification.json    # URL validation results
├── site/
│   └── index.html           # The deliverable — self-contained HTML page
├── run.py                   # Main entry point for the pipeline
└── requirements.txt
```

## How to Run

### Prerequisites
- Python 3.12+
- API keys in `.env`:
  ```
  LLM_API_KEY=your-azure-openai-key
  LLM_API_BASE=https://your-resource.openai.azure.com/
  LLM_API_VERSION=2024-12-01-preview
  LLM_MODEL_NAME=azure/gpt-4o-mini
  TAVILY_API_KEY=your-tavily-key
  COMPOSIO_API_KEY=your-composio-key  # optional, for cross-reference
  ```

### Install & Run
```bash
pip install -r requirements.txt
python run.py all          # Full pipeline: research → verify → patterns → export
python run.py research     # Just the research step (resumes from where it left off)
python run.py export       # Just regenerate the HTML
```

### Resume Support
The orchestrator saves results incrementally. If interrupted, just run again — it skips already-completed apps.

## Architecture

```
┌─────────────┐     ┌────────────┐     ┌──────────────┐
│  Tavily      │────▶│ GPT-4o-mini│────▶│  Structured  │
│  Web Search  │     │ (Azure)    │     │  JSON Output │
│  3 queries/  │     │ Function   │     │  per app     │
│  app         │     │ Calling    │     │              │
└─────────────┘     └────────────┘     └──────┬───────┘
                                              │
                    ┌────────────┐     ┌──────▼───────┐
                    │ Composio   │────▶│ Orchestrator │
                    │ SDK Check  │     │ 100 apps     │
                    └────────────┘     │ resume/retry │
                                       └──────┬───────┘
                                              │
                    ┌────────────┐     ┌──────▼───────┐
                    │ URL HEAD   │────▶│ Verifier     │
                    │ Validation │     │ + spot-check │
                    └────────────┘     └──────┬───────┘
                                              │
                    ┌────────────┐     ┌──────▼───────┐
                    │ Pattern    │────▶│ HTML Export   │
                    │ Analysis   │     │ Self-contained│
                    └────────────┘     └──────────────┘
```

## Verification

- **URL Validation**: HTTP HEAD requests to all 300 evidence URLs — 93% reachable
- **Spot-Check Framework**: Stratified 15-app sample (5 well-known, 5 mid-tier, 5 niche)
- **Composio Cross-Reference**: SDK-verified which 57 apps already have Composio toolkits

### Limitations (Honest Assessment)
- MCP server detection has false positives — web search often conflates mentions with actual availability
- Self-serve classification can be ambiguous for "contact sales for API, but free product tier" apps
- Low-confidence results (fanbasis 0.5, iPayX 0.2, Sherlock 0.6) need manual verification
- Evidence URLs may become stale as documentation pages change

## Tech Stack

- **LLM**: Azure GPT-4o-mini (via OpenAI Python SDK)
- **Search**: Tavily API (3 queries per app)
- **Structured Output**: OpenAI function calling with JSON schema
- **Cross-Reference**: Composio Python SDK
- **Deliverable**: Vanilla HTML/CSS/JS — no build step, no external dependencies

Built by Vatsal Kumar(kumarvatsal34@gmail.com)
