import os
import json
from openai import AzureOpenAI
from tavily import TavilyClient
from .schemas import RESEARCH_TOOL_SCHEMA, AppResearch


SYSTEM_PROMPT = """You are a research analyst investigating software apps for Composio, a platform that builds agent toolkits for apps. You will be given web search results about an app. From those results, extract:

1. **Authentication methods**: How does the API authenticate? (OAuth2, API Key, Basic Auth, Token, JWT, HMAC, etc.)
2. **Self-serve access**: Can a developer sign up and get API credentials on their own (free tier or free trial), or is it gated behind sales/partnership/admin approval?
3. **API surface**: What type of API (REST, GraphQL, etc.)? How broad is the coverage (Broad = most features, Moderate = core features, Narrow = few endpoints)?
4. **MCP server**: Does an MCP (Model Context Protocol) server exist for this app?
5. **Buildability**: Could Composio build an agent toolkit today? "Ready" = public API + self-serve + standard auth. "Ready with caveats" = possible but has friction. "Blocked" = no public API or requires partnership.

IMPORTANT RULES:
- Only use information from the provided search results. Cite actual URLs from the results.
- If you cannot find information, say "Unknown" rather than guessing.
- Rate your confidence honestly (0.0-1.0). Lower if results were sparse.
- For auth_methods, ONLY use values from this list: OAuth2, API Key, Basic, Token, JWT, HMAC, Other, None. Map any non-standard methods to the closest match (e.g. "Client credentials" -> "OAuth2", "Bearer token" -> "Token").
- You MUST call the record_app_research tool with your findings. Do not respond with text."""


def _search(tavily: TavilyClient, query: str, max_results: int = 5) -> str:
    try:
        results = tavily.search(query=query, max_results=max_results, search_depth="basic")
        snippets = []
        for r in results.get("results", []):
            snippets.append(f"URL: {r['url']}\nTitle: {r['title']}\nSnippet: {r['content']}\n")
        return "\n---\n".join(snippets) if snippets else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def build_user_prompt(app: dict, search_results: str) -> str:
    return (
        f"Research the app \"{app['name']}\" (category: {app['category']}, website: {app['hint']}).\n\n"
        f"Here are web search results about this app's API and developer access:\n\n"
        f"{search_results}\n\n"
        f"Based on these search results, call the record_app_research tool with ALL findings. "
        f"Remember: auth_methods must ONLY contain values from [OAuth2, API Key, Basic, Token, JWT, HMAC, Other, None]."
    )


def research_app(app: dict, openai_client: AzureOpenAI | None = None, tavily_client: TavilyClient | None = None) -> AppResearch:
    if openai_client is None:
        openai_client = AzureOpenAI(
            azure_endpoint=os.environ["LLM_API_BASE"],
            api_key=os.environ["LLM_API_KEY"],
            api_version=os.environ["LLM_API_VERSION"],
        )
    if tavily_client is None:
        tavily_client = TavilyClient()

    # Phase 1: Search with Tavily
    queries = [
        f"{app['name']} API documentation authentication developer",
        f"{app['name']} pricing free tier developer portal API access",
        f"{app['name']} MCP server model context protocol",
    ]
    all_results = []
    for q in queries:
        all_results.append(f"=== Search: {q} ===\n{_search(tavily_client, q, max_results=3)}")
    search_text = "\n\n".join(all_results)

    # Phase 2: Extract structured data with OpenAI
    tools = [RESEARCH_TOOL_SCHEMA]

    response = openai_client.chat.completions.create(
        model=os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini").replace("azure/", ""),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(app, search_text)},
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "record_app_research"}},
        max_completion_tokens=4000,
    )

    msg = response.choices[0].message
    if msg.tool_calls:
        for tc in msg.tool_calls:
            if tc.function.name == "record_app_research":
                data = json.loads(tc.function.arguments)
                return _parse_result(app, data)

    raise RuntimeError(f"Failed to get structured result for {app['name']}")


def _parse_result(app: dict, data: dict) -> AppResearch:
    # Sanitize auth_methods to only allowed values
    allowed_auth = {"OAuth2", "API Key", "Basic", "Token", "JWT", "HMAC", "Other", "None"}
    auth_methods = [m if m in allowed_auth else "Other" for m in data.get("auth_methods", [])]

    return AppResearch(
        app_name=data.get("app_name", app["name"]),
        category=app["category"],
        one_line_description=data.get("one_line_description", ""),
        auth_methods=auth_methods,
        auth_details=data.get("auth_details", ""),
        auth_evidence_url=data.get("auth_evidence_url", ""),
        self_serve=data.get("self_serve", False),
        self_serve_detail=data.get("self_serve_detail", ""),
        self_serve_evidence_url=data.get("self_serve_evidence_url", ""),
        api_type=data.get("api_type", "Unknown"),
        api_breadth=data.get("api_breadth", "Unknown"),
        api_breadth_detail=data.get("api_breadth_detail", ""),
        api_evidence_url=data.get("api_evidence_url", ""),
        has_mcp_server=data.get("has_mcp_server", False),
        mcp_server_detail=data.get("mcp_server_detail", ""),
        buildability_verdict=data.get("buildability_verdict", "Blocked"),
        buildability_blocker=data.get("buildability_blocker", ""),
        buildability_detail=data.get("buildability_detail", ""),
        confidence=data.get("confidence", 0.5),
    )
