from pydantic import BaseModel


class AppResearch(BaseModel):
    app_name: str
    category: str
    one_line_description: str
    auth_methods: list[str]
    auth_details: str
    auth_evidence_url: str
    self_serve: bool
    self_serve_detail: str
    self_serve_evidence_url: str
    api_type: str
    api_breadth: str
    api_breadth_detail: str
    api_evidence_url: str
    has_mcp_server: bool
    mcp_server_detail: str
    buildability_verdict: str
    buildability_blocker: str
    buildability_detail: str
    confidence: float


RESEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "record_app_research",
        "description": "Record the structured research findings for an app.",
        "parameters": {
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of the app"},
            "one_line_description": {"type": "string", "description": "What the app does in one line"},
            "auth_methods": {
                "type": "array",
                "items": {"type": "string", "enum": ["OAuth2", "API Key", "Basic", "Token", "JWT", "HMAC", "Other", "None"]},
                "description": "Authentication methods supported",
            },
            "auth_details": {"type": "string", "description": "Details about authentication (e.g. OAuth2 with PKCE, API key in header, etc.)"},
            "auth_evidence_url": {"type": "string", "description": "URL to the docs page about authentication"},
            "self_serve": {"type": "boolean", "description": "True if a developer can get credentials themselves for free or on a free trial without admin approval or partnership"},
            "self_serve_detail": {"type": "string", "description": "Details: free tier, trial length, credit card required, admin approval needed, partnership/contact-sales gate, etc."},
            "self_serve_evidence_url": {"type": "string", "description": "URL to pricing/signup page used as evidence"},
            "api_type": {"type": "string", "enum": ["REST", "GraphQL", "REST+GraphQL", "SOAP", "gRPC", "WebSocket", "CLI-only", "No public API", "Other"], "description": "Type of public API"},
            "api_breadth": {"type": "string", "enum": ["Broad", "Moderate", "Narrow", "Unknown"], "description": "How broad the API surface is. Broad = covers most product features. Moderate = covers core features. Narrow = limited endpoints."},
            "api_breadth_detail": {"type": "string", "description": "Brief description of what the API covers and roughly how many endpoints/resources"},
            "api_evidence_url": {"type": "string", "description": "URL to the API reference or developer docs"},
            "has_mcp_server": {"type": "boolean", "description": "Whether an MCP (Model Context Protocol) server exists for this app"},
            "mcp_server_detail": {"type": "string", "description": "Details about MCP server: official vs community, what it covers, link if found"},
            "buildability_verdict": {"type": "string", "enum": ["Ready", "Ready with caveats", "Blocked"], "description": "Could Composio build an agent toolkit for this app today?"},
            "buildability_blocker": {"type": "string", "description": "Main blocker if not Ready (e.g. 'No public API', 'Partnership required', 'Complex auth', etc.). Empty string if Ready."},
            "buildability_detail": {"type": "string", "description": "Explanation of the verdict and any caveats"},
            "confidence": {"type": "number", "description": "Self-assessed confidence in findings from 0.0 to 1.0. Lower if docs were sparse or ambiguous."},
        },
        "required": [
            "app_name", "one_line_description", "auth_methods", "auth_details",
            "auth_evidence_url", "self_serve", "self_serve_detail", "self_serve_evidence_url",
            "api_type", "api_breadth", "api_breadth_detail", "api_evidence_url",
            "has_mcp_server", "mcp_server_detail", "buildability_verdict",
            "buildability_blocker", "buildability_detail", "confidence",
        ],
    },
},
}
