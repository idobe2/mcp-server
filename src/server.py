from __future__ import annotations

import os
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

import json
from openai import OpenAI


# MCP server (FastMCP) – high level API
mcp = FastMCP("CSV Sales Analyzer", json_response=True)

# OpenAI client
openai_client = OpenAI()


# ---------
# Models (Input / Output Schemas)
# ---------
class FilterParams(BaseModel):
    start_date: Optional[str] = Field(
        default=None, description="YYYY-MM-DD (inclusive). Example: 2024-01-01"
    )
    end_date: Optional[str] = Field(
        default=None, description="YYYY-MM-DD (inclusive). Example: 2024-12-31"
    )
    region: Optional[list[str]] = Field(default=None, description="Filter by Region values")
    product_category: Optional[list[str]] = Field(default=None, description="Filter by Product Category values")
    payment_method: Optional[list[str]] = Field(default=None, description="Filter by Payment Method values")
    product_name_contains: Optional[str] = Field(default=None, description="Substring match for Product Name")
    limit: int = Field(default=200, ge=1, le=2000, description="Max preview rows returned")


class FilteredData(BaseModel):
    row_count: int
    columns: list[str]
    preview: list[dict[str, Any]]


class GroupMetric(BaseModel):
    name: str
    revenue: float
    units: int
    orders: int


class ProductMetric(BaseModel):
    product_name: str
    revenue: float
    units: int
    orders: int


class KPISummary(BaseModel):
    applied_filters: FilterParams
    row_count: int
    orders_count: int
    total_units: int
    total_revenue: float
    avg_unit_price_simple: float
    avg_unit_price_weighted: float
    revenue_by_category: list[GroupMetric]
    revenue_by_region: list[GroupMetric]
    top_products_by_revenue: list[ProductMetric]


class InsightsReport(BaseModel):
    note: str
    insights: list[str]
    summary: str
    recommendations: list[str]


# ---------
# Helpers
# ---------
def _load_df() -> pd.DataFrame:
    csv_path = os.getenv("CSV_PATH", os.path.join("data", "Online Sales Data.csv"))
    df = pd.read_csv(csv_path)

    # Normalize columns we know exist in your file
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Units Sold"] = pd.to_numeric(df["Units Sold"], errors="coerce").fillna(0).astype(int)
    df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce").fillna(0.0)
    df["Total Revenue"] = pd.to_numeric(df["Total Revenue"], errors="coerce").fillna(0.0)

    return df


def _apply_filters(df: pd.DataFrame, f: FilterParams) -> pd.DataFrame:
    out = df.copy()

    if f.start_date:
        start = pd.to_datetime(f.start_date)
        out = out[out["Date"] >= start]

    if f.end_date:
        end = pd.to_datetime(f.end_date)
        out = out[out["Date"] <= end]

    if f.region:
        out = out[out["Region"].isin(f.region)]

    if f.product_category:
        out = out[out["Product Category"].isin(f.product_category)]

    if f.payment_method:
        out = out[out["Payment Method"].isin(f.payment_method)]

    if f.product_name_contains:
        needle = f.product_name_contains.strip().lower()
        out = out[out["Product Name"].astype(str).str.lower().str.contains(needle, na=False)]

    return out


def _group_metrics(df: pd.DataFrame, group_col: str, top_n: int = 10) -> list[GroupMetric]:
    g = (
        df.groupby(group_col, dropna=False)
        .agg(revenue=("Total Revenue", "sum"), units=("Units Sold", "sum"), orders=("Transaction ID", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )

    return [
        GroupMetric(
            name=str(row[group_col]),
            revenue=float(row["revenue"]),
            units=int(row["units"]),
            orders=int(row["orders"]),
        )
        for _, row in g.iterrows()
    ]


# ---------
# Tools
# ---------
@mcp.tool()
def filter_sales_data(filters: FilterParams) -> FilteredData:
    """Return filtered rows preview from the sales CSV."""
    df = _load_df()
    filtered = _apply_filters(df, filters)

    preview_df = filtered.head(filters.limit)
    return FilteredData(
        row_count=int(filtered.shape[0]),
        columns=list(filtered.columns),
        preview=preview_df.to_dict(orient="records"),
    )


@mcp.tool()
def compute_sales_kpis(filters: FilterParams) -> KPISummary:
    """Compute KPI aggregates from the sales CSV (after applying filters)."""
    df = _load_df()
    filtered = _apply_filters(df, filters)

    row_count = int(filtered.shape[0])
    orders_count = int(filtered["Transaction ID"].nunique()) if row_count else 0
    total_units = int(filtered["Units Sold"].sum()) if row_count else 0
    total_revenue = float(filtered["Total Revenue"].sum()) if row_count else 0.0

    avg_unit_price_simple = float(filtered["Unit Price"].mean()) if row_count else 0.0
    avg_unit_price_weighted = float(total_revenue / total_units) if total_units else 0.0

    revenue_by_category = _group_metrics(filtered, "Product Category", top_n=10) if row_count else []
    revenue_by_region = _group_metrics(filtered, "Region", top_n=10) if row_count else []

    top_products = []
    if row_count:
        g = (
            filtered.groupby("Product Name", dropna=False)
            .agg(revenue=("Total Revenue", "sum"), units=("Units Sold", "sum"), orders=("Transaction ID", "count"))
            .reset_index()
            .sort_values("revenue", ascending=False)
            .head(10)
        )
        top_products = [
            ProductMetric(
                product_name=str(row["Product Name"]),
                revenue=float(row["revenue"]),
                units=int(row["units"]),
                orders=int(row["orders"]),
            )
            for _, row in g.iterrows()
        ]

    return KPISummary(
        applied_filters=filters,
        row_count=row_count,
        orders_count=orders_count,
        total_units=total_units,
        total_revenue=total_revenue,
        avg_unit_price_simple=avg_unit_price_simple,
        avg_unit_price_weighted=avg_unit_price_weighted,
        revenue_by_category=revenue_by_category,
        revenue_by_region=revenue_by_region,
        top_products_by_revenue=top_products,
    )


@mcp.tool()
def openai_generate_insights(
    kpis: KPISummary,
    question: str = "Give analytical insights and recommendations based on the KPIs only."
) -> InsightsReport:
    """
    Uses OpenAI to generate analytical insights from the KPI summary.
    """

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

    # Pydantic v1/v2 compatibility
    kpis_dict = kpis.model_dump() if hasattr(kpis, "model_dump") else kpis.dict()

    system_instructions = (
    "You are a business data analyst. Answer in an analytical (not creative) style. "
    "Use only the data provided in the KPI. "
    "If information is missing—specify that it cannot be inferred. "
    "Each Insight should include numbers/percentages when possible. "
    "Return structured output according to the given schema."
    )

    user_content = (
        f"Question: {question}\n\n"
        f"KPI (JSON):\n{json.dumps(kpis_dict, ensure_ascii=False)}"
    )

    # Structured output (Pydantic schema)
    response = openai_client.responses.parse(
        model=model,
        temperature=temperature,
        input=[
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_content},
        ],
        text_format=InsightsReport,
        max_output_tokens=700,
    )
    return response.output_parsed



if __name__ == "__main__":
    # Recommended transport for local testing with inspector
    mcp.run(transport="streamable-http")
