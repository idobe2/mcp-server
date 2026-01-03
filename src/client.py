import asyncio
from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client
import json
import ast



MCP_URL = "http://127.0.0.1:8000/mcp"

def _parse_text_payload(text: str) -> dict:
    text = text.strip()

    # 1) Try JSON
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 2) Try Python literal dict (single quotes, etc.)
    try:
        obj = ast.literal_eval(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 3) Fallback
    return {"text": text}


def _extract_structured(result) -> dict:
    sc = getattr(result, "structuredContent", None)
    if sc and isinstance(sc, dict) and len(sc.keys()) > 0:
        return sc

    content = getattr(result, "content", None) or []
    texts = []

    for c in content:
        if isinstance(c, types.TextContent):
            texts.append(c.text)
        elif isinstance(c, dict) and c.get("type") == "text":
            texts.append(c.get("text", ""))

    combined = "\n".join([t for t in texts if t])
    if combined:
        return _parse_text_payload(combined)

    return {}





async def main():
    # 1) call computational tool
    filters = {
        # Filters example (leave empty for no filters)
        # "start_date": "2024-01-01",
        # "end_date": "2024-12-31",
        # "region": ["Europe"],
        # "product_category": ["Electronics"],
        # "payment_method": ["Credit Card"],
        # "product_name_contains": "Laptop",
        "limit": 200,
    }

    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()

            kpi_call = await session.call_tool(
                "compute_sales_kpis",
                arguments={"filters": filters},
            )
            kpis = _extract_structured(kpi_call)

            # 2) send to OpenAI tool
            question = "Analyze the data: Provide 5 Insights with numbers, a short summary, and 3 actionable recommendations."
            ai_call = await session.call_tool(
                "openai_generate_insights",
                arguments={"kpis": kpis, "question": question},
            )
            print("DEBUG has structuredContent:", hasattr(ai_call, "structuredContent"))
            print("DEBUG has structured_content:", hasattr(ai_call, "structured_content"))
            report = _extract_structured(ai_call)
            print("DEBUG report keys:", list(report.keys()))
            if report.keys() == {"text"}:
                print("\nDEBUG RAW REPORT TEXT (first 800 chars):")
                print(report["text"][:800])


    # 3) print output
    print("\n=== INSIGHTS ===")
    for i, item in enumerate(report.get("insights", []), 1):
        print(f"{i}. {item}")

    print("\n=== SUMMARY ===")
    print(report.get("summary", ""))

    print("\n=== RECOMMENDATIONS ===")
    for i, item in enumerate(report.get("recommendations", []), 1):
        print(f"{i}. {item}")


if __name__ == "__main__":
    asyncio.run(main())
