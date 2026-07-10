import json
import html
import math
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SITE_DIR = Path(__file__).resolve().parent.parent / "site"


def load_json(name: str) -> dict | list:
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def esc(text) -> str:
    return html.escape(str(text))


def build_html(research: list[dict], patterns: dict, verification: dict | None = None) -> str:
    total = len(research)
    auth_dist = patterns.get("auth_distribution", {}).get("overall", {})
    ss = patterns.get("self_serve", {})
    bv = patterns.get("buildability", {}).get("verdicts", {})
    easy_wins = patterns.get("easy_wins", [])
    mcp = patterns.get("mcp_coverage", {})
    confidence = patterns.get("confidence", {})
    needs_outreach = patterns.get("needs_outreach", [])
    blockers = patterns.get("buildability", {}).get("top_blockers", {})

    dominant_auth = max(auth_dist, key=auth_dist.get) if auth_dist else "N/A"
    self_serve_pct = ss.get("overall_rate", 0)
    ready_count = bv.get("Ready", 0)
    caveat_count = bv.get("Ready with caveats", 0)
    blocked_count = bv.get("Blocked", 0)

    composio_count = sum(1 for r in research if r.get("composio_supported"))
    composio_gaps = [r for r in research if not r.get("composio_supported") and r.get("buildability_verdict") == "Ready"]

    url_stats = {}
    if verification:
        url_stats = verification.get("url_validation", {}).get("stats", {})

    # Table rows
    rows = []
    for r in sorted(research, key=lambda x: (x["category"], x["app_name"])):
        auth_badges = "".join(f'<span class="badge badge-auth">{esc(a)}</span>' for a in r.get("auth_methods", []))
        ss_val = r.get("self_serve", False)
        vc = r.get("buildability_verdict", "Unknown")
        vc_cls = {"Ready": "ready", "Ready with caveats": "caveat", "Blocked": "blocked"}.get(vc, "unknown")
        mcp_val = r.get("has_mcp_server", False)
        conf = r.get("confidence", 0)
        composio = r.get("composio_supported", False)

        evidence = []
        for field, label in [("auth_evidence_url", "Auth"), ("api_evidence_url", "API"), ("self_serve_evidence_url", "Pricing")]:
            url = r.get(field, "")
            if url and url.lower() not in ("", "n/a", "unknown", "none"):
                evidence.append(f'<a href="{esc(url)}" target="_blank" rel="noopener">{label}</a>')

        rows.append(f'''<tr data-cat="{esc(r['category'])}" data-v="{vc_cls}" data-ss="{int(ss_val)}" data-comp="{int(composio)}">
<td><strong>{esc(r['app_name'])}</strong><br><span class="sub">{esc(r.get('one_line_description','')[:60])}</span></td>
<td><span class="cat-pill">{esc(r['category'].split(' and ')[0].split(',')[0])}</span></td>
<td>{auth_badges}</td>
<td class="center"><span class="icon {'green' if ss_val else 'red'}">{'&#10003;' if ss_val else '&#10007;'}</span></td>
<td>{esc(r.get('api_type', ''))}<br><span class="sub">{esc(r.get('api_breadth', ''))}</span></td>
<td class="center"><span class="icon {'green' if mcp_val else 'dim'}">{'&#10003;' if mcp_val else '—'}</span></td>
<td><span class="verdict-pill {vc_cls}">{esc(vc)}</span></td>
<td class="center"><span class="icon {'green' if composio else 'dim'}">{'&#10003;' if composio else '—'}</span></td>
<td class="center conf-{('high' if conf >= 0.7 else 'mid' if conf >= 0.4 else 'low')}">{conf:.0%}</td>
<td class="links">{' '.join(evidence)}</td>
</tr>''')

    # Easy wins for the recommendation section
    gap_items = "\n".join(
        f'<div class="gap-card"><strong>{esc(r["app_name"])}</strong><span class="sub">{esc(r["category"])}</span><span class="badge badge-auth">{", ".join(r.get("auth_methods",[]))}</span></div>'
        for r in composio_gaps[:12]
    )

    ew_items = "\n".join(
        f'<div class="gap-card"><strong>{esc(w["app_name"])}</strong><span class="sub">{esc(w["category"])}</span><span class="badge badge-auth">{", ".join(w["auth_methods"])}</span></div>'
        for w in easy_wins[:12]
    )

    blocker_items = "\n".join(
        f'<div class="blocker-row"><span class="blocker-name">{esc(b)}</span><span class="blocker-bar" style="width:{int(c/max(blockers.values())*100)}%"></span><span class="blocker-count">{c}</span></div>'
        for b, c in list(blockers.items())[:8]
    ) if blockers else '<p class="dim">No blockers identified.</p>'

    outreach_items = "\n".join(
        f'<tr><td>{esc(o["app_name"])}</td><td>{esc(o.get("blocker","Gated"))}</td></tr>'
        for o in needs_outreach[:12]
    )

    verif_section = ""
    if url_stats:
        verif_section = f'''
<div class="metric-grid">
<div class="metric"><span class="metric-num green">{url_stats.get('reachable_pct',0)}%</span><span class="metric-label">URLs Reachable</span></div>
<div class="metric"><span class="metric-num">{url_stats.get('reachable',0)}</span><span class="metric-label">Valid Evidence URLs</span></div>
<div class="metric"><span class="metric-num red">{url_stats.get('broken',0)}</span><span class="metric-label">Broken URLs</span></div>
</div>
<p class="note">Evidence URLs were validated via HTTP HEAD requests. {url_stats.get('reachable_pct',0)}% of cited documentation links are live and accessible.</p>'''

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Composio App Research — 100 Apps Analyzed</title>
<style>
:root {{
  --bg: #fafbfc; --bg2: #ffffff; --fg: #1a1a2e; --fg2: #4a5568; --border: #e2e8f0;
  --accent: #6366f1; --accent-soft: #eef2ff; --green: #10b981; --green-soft: #d1fae5;
  --yellow: #f59e0b; --yellow-soft: #fef3c7; --red: #ef4444; --red-soft: #fee2e2;
  --purple: #8b5cf6; --purple-soft: #ede9fe;
  --radius: 12px; --shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-lg: 0 10px 25px rgba(0,0,0,.08);
  --font: 'Inter', system-ui, -apple-system, sans-serif;
  --mono: 'JetBrains Mono', 'Fira Code', monospace;
}}
@media (prefers-color-scheme:dark) {{
  :root {{ --bg:#0b1121; --bg2:#151d33; --fg:#e2e8f0; --fg2:#94a3b8; --border:#1e293b;
    --accent-soft:#1e1b4b; --green-soft:#064e3b; --yellow-soft:#451a03; --red-soft:#450a0a; --purple-soft:#2e1065;
    --shadow:0 1px 3px rgba(0,0,0,.3); --shadow-lg:0 10px 25px rgba(0,0,0,.4); }}
}}
[data-theme="dark"] {{ --bg:#0b1121; --bg2:#151d33; --fg:#e2e8f0; --fg2:#94a3b8; --border:#1e293b;
  --accent-soft:#1e1b4b; --green-soft:#064e3b; --yellow-soft:#451a03; --red-soft:#450a0a; --purple-soft:#2e1065;
  --shadow:0 1px 3px rgba(0,0,0,.3); --shadow-lg:0 10px 25px rgba(0,0,0,.4); }}
[data-theme="light"] {{ --bg:#fafbfc; --bg2:#ffffff; --fg:#1a1a2e; --fg2:#4a5568; --border:#e2e8f0;
  --accent-soft:#eef2ff; --green-soft:#d1fae5; --yellow-soft:#fef3c7; --red-soft:#fee2e2; --purple-soft:#ede9fe;
  --shadow:0 1px 3px rgba(0,0,0,.06); --shadow-lg:0 10px 25px rgba(0,0,0,.08); }}

* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:var(--font); background:var(--bg); color:var(--fg); line-height:1.6; }}
.wrap {{ max-width:1300px; margin:0 auto; padding:0 1.5rem; }}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}

/* Header */
.hero {{ padding:3rem 0 2rem; text-align:center; border-bottom:1px solid var(--border); }}
.hero h1 {{ font-size:2.2rem; font-weight:800; letter-spacing:-.02em;
  background:linear-gradient(135deg,var(--accent),var(--purple));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
.hero p {{ color:var(--fg2); margin:.5rem 0 0; font-size:1.05rem; }}
.theme-btn {{ position:fixed; top:1rem; right:1rem; z-index:999; background:var(--bg2); border:1px solid var(--border);
  border-radius:50%; width:40px; height:40px; cursor:pointer; font-size:1.2rem; display:flex; align-items:center; justify-content:center;
  box-shadow:var(--shadow); transition:.2s; }}
.theme-btn:hover {{ transform:scale(1.1); }}

/* Stats */
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1rem; margin:2rem 0; }}
.stat {{ background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius); padding:1.2rem; text-align:center; box-shadow:var(--shadow); }}
.stat-val {{ font-size:1.8rem; font-weight:800; color:var(--accent); }}
.stat-val.green {{ color:var(--green); }}
.stat-val.purple {{ color:var(--purple); }}
.stat-label {{ font-size:.75rem; color:var(--fg2); margin-top:.25rem; text-transform:uppercase; letter-spacing:.05em; }}

/* Sections */
section {{ margin:3rem 0; }}
.section-title {{ font-size:1.4rem; font-weight:700; margin-bottom:1.5rem; display:flex; align-items:center; gap:.5rem; }}
.section-title::before {{ content:''; display:block; width:4px; height:24px; background:var(--accent); border-radius:2px; }}

/* Cards grid */
.card-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1.5rem; }}
.card {{ background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius); padding:1.5rem; box-shadow:var(--shadow); }}
.card h3 {{ font-size:1rem; margin-bottom:.75rem; }}

/* Charts */
.chart-container {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:1.5rem; margin:1.5rem 0; }}
.chart-card {{ background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius); padding:1.5rem; box-shadow:var(--shadow); }}
.chart-card h3 {{ font-size:.9rem; font-weight:600; margin-bottom:1rem; color:var(--fg2); text-transform:uppercase; letter-spacing:.03em; }}
.bar-row {{ display:flex; align-items:center; gap:.5rem; margin:.4rem 0; }}
.bar-label {{ width:80px; font-size:.8rem; text-align:right; color:var(--fg2); flex-shrink:0; }}
.bar-track {{ flex:1; height:24px; background:var(--border); border-radius:6px; overflow:hidden; position:relative; }}
.bar-fill {{ height:100%; border-radius:6px; transition:width .5s ease; }}
.bar-val {{ position:absolute; right:8px; top:50%; transform:translateY(-50%); font-size:.7rem; font-weight:600; color:var(--fg); }}
.donut-wrap {{ display:flex; align-items:center; justify-content:center; gap:1.5rem; flex-wrap:wrap; }}
.donut-legend {{ display:flex; flex-direction:column; gap:.5rem; }}
.legend-item {{ display:flex; align-items:center; gap:.5rem; font-size:.85rem; }}
.legend-dot {{ width:12px; height:12px; border-radius:50%; }}

/* Gap cards */
.gap-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:.75rem; }}
.gap-card {{ background:var(--bg2); border:1px solid var(--border); border-radius:8px; padding:.75rem 1rem;
  display:flex; flex-direction:column; gap:.25rem; }}
.gap-card strong {{ font-size:.85rem; }}

/* Blockers */
.blocker-row {{ display:flex; align-items:center; gap:.75rem; margin:.5rem 0; }}
.blocker-name {{ width:180px; font-size:.8rem; color:var(--fg2); flex-shrink:0; text-align:right; }}
.blocker-bar {{ height:20px; background:linear-gradient(90deg,var(--red),var(--yellow)); border-radius:4px; min-width:4px; }}
.blocker-count {{ font-size:.75rem; font-weight:600; }}

/* Metrics */
.metric-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:1rem; margin:1rem 0; }}
.metric {{ text-align:center; }}
.metric-num {{ font-size:1.5rem; font-weight:800; }}
.metric-label {{ font-size:.7rem; color:var(--fg2); text-transform:uppercase; }}

/* Table */
.table-section {{ background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius); overflow:hidden; box-shadow:var(--shadow); }}
.toolbar {{ display:flex; gap:.5rem; flex-wrap:wrap; padding:1rem 1.5rem; border-bottom:1px solid var(--border); align-items:center; }}
.toolbar select, .toolbar input {{ padding:.5rem .75rem; border:1px solid var(--border); border-radius:8px; background:var(--bg);
  color:var(--fg); font-size:.8rem; outline:none; }}
.toolbar select:focus, .toolbar input:focus {{ border-color:var(--accent); }}
.toolbar .count {{ margin-left:auto; font-size:.8rem; color:var(--fg2); }}
.table-wrap {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:.8rem; }}
th {{ padding:.6rem .75rem; text-align:left; background:var(--bg); border-bottom:2px solid var(--border);
  font-size:.7rem; text-transform:uppercase; letter-spacing:.04em; color:var(--fg2); cursor:pointer; white-space:nowrap; user-select:none; }}
th:hover {{ color:var(--accent); }}
td {{ padding:.6rem .75rem; border-bottom:1px solid var(--border); vertical-align:top; }}
tr:hover {{ background:var(--accent-soft); }}
.sub {{ font-size:.7rem; color:var(--fg2); }}
.center {{ text-align:center; }}
.icon {{ font-weight:700; }}
.icon.green {{ color:var(--green); }}
.icon.red {{ color:var(--red); }}
.icon.dim {{ color:var(--border); }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:.65rem; font-weight:600; margin:1px; white-space:nowrap; }}
.badge-auth {{ background:var(--accent-soft); color:var(--accent); }}
.cat-pill {{ background:var(--purple-soft); color:var(--purple); padding:2px 8px; border-radius:10px; font-size:.65rem; font-weight:600; white-space:nowrap; }}
.verdict-pill {{ padding:3px 10px; border-radius:10px; font-size:.7rem; font-weight:600; white-space:nowrap; }}
.verdict-pill.ready {{ background:var(--green-soft); color:var(--green); }}
.verdict-pill.caveat {{ background:var(--yellow-soft); color:var(--yellow); }}
.verdict-pill.blocked {{ background:var(--red-soft); color:var(--red); }}
.conf-high {{ color:var(--green); font-weight:600; }}
.conf-mid {{ color:var(--yellow); font-weight:600; }}
.conf-low {{ color:var(--red); font-weight:600; }}
.links {{ font-size:.7rem; white-space:nowrap; }}
.links a {{ margin-right:.5rem; }}

/* Agent section */
.agent-card {{ background:linear-gradient(135deg,var(--accent-soft),var(--purple-soft)); border:1px solid var(--border);
  border-radius:var(--radius); padding:2rem; box-shadow:var(--shadow); }}
.agent-card h3 {{ margin:.75rem 0 .5rem; font-size:.95rem; }}
.agent-card ul {{ padding-left:1.2rem; font-size:.85rem; color:var(--fg2); }}
.agent-card li {{ margin:.3rem 0; }}
.agent-card code {{ background:var(--bg); padding:2px 6px; border-radius:4px; font-family:var(--mono); font-size:.75rem; }}

.note {{ font-size:.8rem; color:var(--fg2); font-style:italic; }}
.dim {{ color:var(--fg2); }}

footer {{ text-align:center; padding:3rem 0; color:var(--fg2); font-size:.75rem; border-top:1px solid var(--border); margin-top:3rem; }}

@media (max-width:768px) {{
  .hero h1 {{ font-size:1.5rem; }}
  .stats {{ grid-template-columns:repeat(2,1fr); }}
  .chart-container {{ grid-template-columns:1fr; }}
  .toolbar {{ flex-direction:column; }}
  td, th {{ padding:.4rem .5rem; }}
}}
</style>
</head>
<body>
<button class="theme-btn" onclick="toggleTheme()" aria-label="Toggle theme">&#9681;</button>
<div class="wrap">

<div class="hero">
<h1>Composio App Research</h1>
<p>Automated analysis of 100 apps across 10 categories — authentication, API surface, buildability verdicts, and integration patterns</p>
</div>

<div class="stats">
<div class="stat"><div class="stat-val">{total}</div><div class="stat-label">Apps Analyzed</div></div>
<div class="stat"><div class="stat-val green">{ready_count}</div><div class="stat-label">Ready to Build</div></div>
<div class="stat"><div class="stat-val">{self_serve_pct}%</div><div class="stat-label">Self-Serve Access</div></div>
<div class="stat"><div class="stat-val purple">{composio_count}</div><div class="stat-label">Already in Composio</div></div>
<div class="stat"><div class="stat-val">{len(composio_gaps)}</div><div class="stat-label">Untapped Ready Apps</div></div>
<div class="stat"><div class="stat-val">{mcp.get('count',0)}</div><div class="stat-label">Have MCP Servers</div></div>
</div>

<section>
<h2 class="section-title">Distribution & Patterns</h2>
<div class="chart-container">
<div class="chart-card">
<h3>Authentication Methods</h3>
{_build_bar_chart(auth_dist, ['#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#ddd6fe','#7c3aed','#4c1d95','#312e81'])}
</div>
<div class="chart-card">
<h3>Buildability Verdicts</h3>
<div class="donut-wrap">
<svg viewBox="0 0 120 120" width="160" height="160">
{_build_donut_svg(bv, {'Ready':'#10b981','Ready with caveats':'#f59e0b','Blocked':'#ef4444'})}
</svg>
<div class="donut-legend">
<div class="legend-item"><span class="legend-dot" style="background:#10b981"></span>Ready ({bv.get('Ready',0)})</div>
<div class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span>Caveats ({bv.get('Ready with caveats',0)})</div>
<div class="legend-item"><span class="legend-dot" style="background:#ef4444"></span>Blocked ({bv.get('Blocked',0)})</div>
</div>
</div>
</div>
<div class="chart-card">
<h3>Self-Serve by Category</h3>
{_build_category_bars(ss.get('by_category',{}))}
</div>
</div>
</section>

<section>
<h2 class="section-title">Actionable Insights</h2>
<div class="card-grid">
<div class="card">
<h3>&#127942; Composio Gaps — Ready but Unsupported</h3>
<p class="note" style="margin-bottom:.75rem">{len(composio_gaps)} apps are "Ready" but not yet in Composio:</p>
<div class="gap-grid">{gap_items if gap_items else '<p class="dim">All ready apps are already supported!</p>'}</div>
</div>
<div class="card">
<h3>&#9889; Easy Wins — Top Toolkit Candidates</h3>
<p class="note" style="margin-bottom:.75rem">Self-serve + REST + standard auth + high confidence:</p>
<div class="gap-grid">{ew_items}</div>
</div>
</div>

<div class="card-grid" style="margin-top:1.5rem">
<div class="card">
<h3>&#128679; Top Buildability Blockers</h3>
{blocker_items}
</div>
<div class="card">
<h3>&#128231; Needs Outreach</h3>
<table style="font-size:.8rem;width:100%">
<tr><th style="background:transparent">App</th><th style="background:transparent">Blocker</th></tr>
{outreach_items}
</table>
</div>
</div>
</section>

<section>
<h2 class="section-title">Research Table</h2>
<div class="table-section">
<div class="toolbar">
<select id="fCat" onchange="ft()"><option value="">All Categories</option></select>
<select id="fVerdict" onchange="ft()"><option value="">All Verdicts</option><option value="ready">Ready</option><option value="caveat">Caveats</option><option value="blocked">Blocked</option></select>
<select id="fSS" onchange="ft()"><option value="">Self-Serve: All</option><option value="1">Yes</option><option value="0">No</option></select>
<select id="fComp" onchange="ft()"><option value="">Composio: All</option><option value="1">Supported</option><option value="0">Not yet</option></select>
<input type="search" id="fSearch" placeholder="Search apps..." oninput="ft()">
<span class="count" id="rowCount">{total} apps</span>
</div>
<div class="table-wrap">
<table id="t">
<thead><tr>
<th onclick="st(0)">App</th>
<th onclick="st(1)">Category</th>
<th>Auth</th>
<th onclick="st(3)">Self-Serve</th>
<th onclick="st(4)">API</th>
<th onclick="st(5)">MCP</th>
<th onclick="st(6)">Verdict</th>
<th onclick="st(7)">Composio</th>
<th onclick="st(8)">Conf</th>
<th>Evidence</th>
</tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>
</div>
</section>

<section>
<h2 class="section-title">The Agent</h2>
<div class="agent-card">
<h3>Architecture</h3>
<ul>
<li><strong>LLM:</strong> Azure GPT-4o-mini via <code>openai.AzureOpenAI</code></li>
<li><strong>Search:</strong> <code>Tavily</code> — 3 targeted queries per app (auth docs, pricing, MCP)</li>
<li><strong>Structured output:</strong> OpenAI function calling with <code>record_app_research</code> tool schema</li>
<li><strong>Composio SDK:</strong> Cross-references which apps already have Composio toolkits via <code>composio.App</code> enum</li>
<li><strong>Resume support:</strong> Incremental JSON saves; skips completed apps on restart</li>
<li><strong>Pipeline:</strong> Research → URL Verification → Pattern Extraction → HTML Export</li>
</ul>
<h3>Verification</h3>
{verif_section}
<h3>Limitations & Honest Assessment</h3>
<ul>
<li>MCP server detection has high false-positive rate — web search often conflates "MCP" mentions with actual server availability</li>
<li>Self-serve assessment can be ambiguous for apps with "contact sales for API access" but free product tiers</li>
<li>Confidence is self-assessed by the model; low-confidence results (fanbasis, iPayX, Sherlock) should be manually verified</li>
<li>Mean confidence: <strong>{confidence.get('mean',0)}</strong> across all apps</li>
</ul>
</div>
</section>

<footer>
Built with Azure GPT-4o-mini + Tavily Search + Composio SDK | Research Agent by Kumar Vatsal | July 2026
</footer>
</div>

<script>
function toggleTheme(){{const r=document.documentElement,c=r.getAttribute('data-theme');r.setAttribute('data-theme',c==='dark'?'light':'dark')}}

const cats=[...new Set([...document.querySelectorAll('#t tbody tr')].map(r=>r.dataset.cat))].sort();
const sel=document.getElementById('fCat');
cats.forEach(c=>{{const o=document.createElement('option');o.value=c;o.textContent=c;sel.appendChild(o)}});

function ft(){{
  const cat=document.getElementById('fCat').value;
  const v=document.getElementById('fVerdict').value;
  const ss=document.getElementById('fSS').value;
  const comp=document.getElementById('fComp').value;
  const q=document.getElementById('fSearch').value.toLowerCase();
  let n=0;
  document.querySelectorAll('#t tbody tr').forEach(r=>{{
    const show=(!cat||r.dataset.cat===cat)&&(!v||r.dataset.v===v)&&(!ss||r.dataset.ss===ss)&&(!comp||r.dataset.comp===comp)&&(!q||r.children[0].textContent.toLowerCase().includes(q));
    r.style.display=show?'':'none';
    if(show)n++;
  }});
  document.getElementById('rowCount').textContent=n+' apps';
}}

let sd={{}};
function st(c){{
  const tb=document.querySelector('#t tbody');
  const rows=[...tb.querySelectorAll('tr')];
  sd[c]=!sd[c];
  rows.sort((a,b)=>{{
    const at=a.children[c].textContent.trim(),bt=b.children[c].textContent.trim();
    const an=parseFloat(at),bn=parseFloat(bt);
    let cmp=(!isNaN(an)&&!isNaN(bn))?an-bn:at.localeCompare(bt);
    return sd[c]?cmp:-cmp;
  }});
  rows.forEach(r=>tb.appendChild(r));
}}
</script>
</body>
</html>'''
    return page


def _build_bar_chart(data: dict, colors: list[str]) -> str:
    if not data:
        return ""
    max_val = max(data.values())
    rows = []
    for i, (label, val) in enumerate(data.items()):
        pct = int(val / max_val * 100)
        color = colors[i % len(colors)]
        rows.append(
            f'<div class="bar-row">'
            f'<span class="bar-label">{esc(label)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}"></div>'
            f'<span class="bar-val">{val}</span></div></div>'
        )
    return "\n".join(rows)


def _build_category_bars(ss_by_cat: dict) -> str:
    rows = []
    for cat, counts in sorted(ss_by_cat.items()):
        yes = counts.get("yes", 0)
        no = counts.get("no", 0)
        total = yes + no
        pct = int(yes / max(total, 1) * 100)
        short = cat.split(" and ")[0].split(",")[0].strip()
        rows.append(
            f'<div class="bar-row">'
            f'<span class="bar-label">{esc(short)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:#10b981"></div>'
            f'<span class="bar-val">{yes}/{total}</span></div></div>'
        )
    return "\n".join(rows)


def _build_donut_svg(data: dict, colors: dict) -> str:
    total = sum(data.values())
    if total == 0:
        return ""
    cx, cy, r = 60, 60, 45
    paths = []
    start = 0
    for label, val in data.items():
        if val == 0:
            continue
        sweep = (val / total) * 360
        end = start + sweep
        large = 1 if sweep > 180 else 0
        x1 = cx + r * math.cos(math.radians(start - 90))
        y1 = cy + r * math.sin(math.radians(start - 90))
        x2 = cx + r * math.cos(math.radians(end - 90))
        y2 = cy + r * math.sin(math.radians(end - 90))
        color = colors.get(label, "#6366f1")
        paths.append(f'<path d="M {cx} {cy} L {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} Z" fill="{color}"/>')
        start = end
    paths.append(f'<circle cx="{cx}" cy="{cy}" r="25" fill="var(--bg2)"/>')
    paths.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--fg)">{total}</text>')
    return "\n".join(paths)


def run():
    research = load_json("research_pass1.json")
    patterns = load_json("patterns.json")
    verification = None
    verif_path = DATA_DIR / "verification.json"
    if verif_path.exists():
        verification = load_json("verification.json")

    page = build_html(research, patterns, verification)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    out = SITE_DIR / "index.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"HTML exported to {out} ({len(page):,} bytes)")
    return out


if __name__ == "__main__":
    run()
