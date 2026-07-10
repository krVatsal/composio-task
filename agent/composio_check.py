"""Check which apps from our list already have Composio toolkits."""
import json
from pathlib import Path
from composio import App

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Known Composio app names mapped to our app list names
COMPOSIO_APP_MAP = {
    "Salesforce": "SALESFORCE", "HubSpot": "HUBSPOT", "Pipedrive": "PIPEDRIVE",
    "Attio": "ATTIO", "Zoho CRM": "ZOHOCRM", "Close": "CLOSE", "Copper": "COPPER",
    "Zendesk": "ZENDESK", "Intercom": "INTERCOM", "Freshdesk": "FRESHDESK",
    "Front": "FRONT", "Help Scout": "HELPSCOUT",
    "Slack": "SLACK", "Twilio": "TWILIO", "Discord": "DISCORD", "Telegram": "TELEGRAM",
    "WhatsApp Business": "WHATSAPP", "Aircall": "AIRCALL",
    "Google Ads": "GOOGLEADS", "Meta Ads": "FACEBOOKADS", "LinkedIn Ads": "LINKEDIN",
    "Mailchimp": "MAILCHIMP", "Klaviyo": "KLAVIYO", "Pinterest": "PINTEREST",
    "SendGrid": "SENDGRID",
    "Shopify": "SHOPIFY", "WooCommerce": "WOOCOMMERCE", "BigCommerce": "BIGCOMMERCE",
    "Squarespace": "SQUARESPACE", "Gumroad": "GUMROAD",
    "Ahrefs": "AHREFS", "Apify": "APIFY", "Firecrawl": "FIRECRAWL",
    "GitHub": "GITHUB", "Vercel": "VERCEL", "Netlify": "NETLIFY",
    "Cloudflare": "CLOUDFLARE", "Supabase": "SUPABASE", "Snowflake": "SNOWFLAKE",
    "Datadog": "DATADOG", "Sentry": "SENTRY",
    "Notion": "NOTION", "Airtable": "AIRTABLE", "Linear": "LINEAR",
    "Jira": "JIRA", "Asana": "ASANA", "Monday.com": "MONDAY", "ClickUp": "CLICKUP",
    "Coda": "CODA", "Smartsheet": "SMARTSHEET", "Harvest": "HARVEST",
    "Stripe": "STRIPE", "Plaid": "PLAID", "Binance": "BINANCE",
    "QuickBooks": "QUICKBOOKS", "Xero": "XERO", "Brex": "BREX",
}


def check_coverage(research: list[dict]) -> list[dict]:
    supported = 0
    for r in research:
        app_name = r["app_name"]
        composio_key = COMPOSIO_APP_MAP.get(app_name)
        if composio_key:
            try:
                _ = getattr(App, composio_key)
                r["composio_supported"] = True
                supported += 1
            except AttributeError:
                r["composio_supported"] = False
        else:
            r["composio_supported"] = False

    print(f"Composio coverage: {supported}/{len(research)} apps already supported")
    return research


def run():
    path = DATA_DIR / "research_pass1.json"
    with open(path, "r", encoding="utf-8") as f:
        research = json.load(f)

    research = check_coverage(research)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(research, f, indent=2, ensure_ascii=False)

    print("Updated research_pass1.json with composio_supported field")
    return research


if __name__ == "__main__":
    run()
