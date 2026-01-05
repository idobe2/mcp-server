import asyncio
import json
from typing import Any, Dict

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "http://127.0.0.1:8000/mcp"


def _extract_structured(result) -> Dict[str, Any]:
    """Prefer structuredContent; fallback to parsing JSON from TextContent."""
    sc = getattr(result, "structuredContent", None)
    if isinstance(sc, dict) and sc:
        return sc

    texts = []
    for c in getattr(result, "content", []) or []:
        if isinstance(c, types.TextContent):
            texts.append(c.text)

    joined = "\n".join(t for t in texts if t).strip()
    if not joined:
        return {}

    try:
        obj = json.loads(joined)
        return obj if isinstance(obj, dict) else {"text": joined}
    except Exception:
        return {"text": joined}


def _raise_if_error(tool_result, tool_name: str) -> None:
    if getattr(tool_result, "isError", False):
        payload = _extract_structured(tool_result)
        raise RuntimeError(f"{tool_name} failed: {payload.get('text', payload)}")


def _print_report(report: Dict[str, Any]) -> None:
    print("\n=== INSIGHTS ===")
    for i, item in enumerate(report.get("insights", []), 1):
        print(f"{i}. {item}")

    print("\n=== SUMMARY ===")
    print(report.get("summary", ""))

    print("\n=== RECOMMENDATIONS ===")
    for i, item in enumerate(report.get("recommendations", []), 1):
        print(f"{i}. {item}")


async def _input(prompt: str) -> str:
    return (await asyncio.to_thread(input, prompt)).strip()


async def main() -> None:
    print("MCP Client REPL")
    print("Commands:")
    print("  :filters   -> set/replace filters JSON")
    print("  :recompute -> recompute KPIs with current filters")
    print("  :kpis      -> print current KPI summary (compact)")
    print("  :exit      -> quit")
    print("")
    print('Example filters JSON: {"region":["Europe"],"start_date":"2024-01-01","end_date":"2024-12-31"}')
    print("")

    filters: Dict[str, Any] = {}
    kpis: Dict[str, Any] = {}

    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def recompute() -> None:
                nonlocal kpis
                res = await session.call_tool("compute_sales_kpis", arguments={"filters": filters})
                _raise_if_error(res, "compute_sales_kpis")
                kpis = _extract_structured(res)
                print(f"\n[KPI recomputed] rows={kpis.get('row_count')} revenue={kpis.get('total_revenue')}\n")

            # compute once at start
            await recompute()

            while True:
                q = await _input("Question> ")
                if not q:
                    continue

                if q in (":exit", "exit", "quit"):
                    break

                if q == ":filters":
                    raw = await _input("Enter filters JSON (empty = {}): ")
                    if not raw:
                        filters = {}
                    else:
                        try:
                            filters = json.loads(raw)
                        except Exception as e:
                            print(f"Invalid JSON: {e}")
                            continue
                    await recompute()
                    continue

                if q == ":recompute":
                    await recompute()
                    continue

                if q == ":kpis":
                    compact = {
                        "row_count": kpis.get("row_count"),
                        "orders_count": kpis.get("orders_count"),
                        "total_units": kpis.get("total_units"),
                        "total_revenue": kpis.get("total_revenue"),
                        "avg_unit_price_simple": kpis.get("avg_unit_price_simple"),
                        "avg_unit_price_weighted": kpis.get("avg_unit_price_weighted"),
                        "top_products_by_revenue": kpis.get("top_products_by_revenue", [])[:3],
                    }
                    print(json.dumps(compact, ensure_ascii=False, indent=2))
                    continue

                res = await session.call_tool(
                    "openai_generate_insights",
                    arguments={"kpis": kpis, "question": q},
                )
                _raise_if_error(res, "openai_generate_insights")
                report = _extract_structured(res)

                if report.keys() == {"text"}:
                    print("\n=== RAW ===")
                    print(report["text"])
                else:
                    _print_report(report)

    print("Bye!")


if __name__ == "__main__":
    asyncio.run(main())
