# MCP CSV Sales Analyzer (With OpenAI)

A course project featuring an MCP server that analyzes sales CSV data and provides:
1) Data filtering capabilities
2) KPI calculation tools  
3) OpenAI-powered insights, summaries, and recommendations based on KPIs

---

## Project Structure

```
mcp-server/
├─ data/
│  └─ Online Sales Data.csv
├─ src/
│  ├─ server.py
│  └─ client.py
├─ images/
├─ .windsurf/
│  └─ workflows/
│     └─ insights.md
├─ analysis.md
├─ csv-sales-analyzer.pbix
├─ requirements.txt
└─ README.md
```

---

## Requirements

- Python 3.10+
- Node.js (only if using the Inspector)
- OpenAI API Key (set as environment variable)

---

## Setup (Windows PowerShell)

### 1) Create Virtual Environment and Install Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Set OpenAI API Key
```powershell
setx OPENAI_API_KEY "sk-..."
```

---

## Running the Application

### 1) Start MCP Server
Run from the project root:
```powershell
cd C:\Users\<yourname>\repos\mcp-server
.\.venv\Scripts\Activate.ps1
python .\src\server.py
```

The server will be available at:
- `http://127.0.0.1:8000/mcp`

> Note: The endpoint requires SSE, so browser access will return 406 (this is expected).

---

## Optional: MCP Inspector (Manual Tool Testing)

In a new terminal:
```powershell
npx -y @modelcontextprotocol/inspector
```

Connection details:
- Transport: `streamable-http`
- URL: `http://127.0.0.1:8000/mcp`

---

## Available Tools (MCP)

The server exposes 3 main tools:

1) `filter_sales_data(filters)`
- Returns filtered records preview and total count

2) `compute_sales_kpis(filters)`  **(Computational Tool)**
- Returns KPIs: revenue, units, orders, averages, breakdown by category/region, and top products

3) `openai_generate_insights(kpis, question)`  **(Uses OpenAI)**
- Processes KPIs (not raw CSV) and returns:
  - Insights (list)
  - Summary (short text)
  - Recommendations (list)

---

## Client Script

The `src/client.py` script:
1) Calls `compute_sales_kpis`
2) Passes results to `openai_generate_insights`
3) Prints Insights, Summary, and Recommendations

To run:
```powershell
.\.venv\Scripts\Activate.ps1
python .\src\client.py
```

---

## Configuration (Optional)

Customize model and temperature via environment variables:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
$env:OPENAI_TEMPERATURE="0.2"
```

---

## Example Output

Sample output from running `client.py`:

```text
=== INSIGHTS ===
1. Total revenue generated is approximately $80,567.85 from 240 orders, indicating an average revenue per order of about $335.69.
2. The average unit price weighted is $155.54, while the average unit price simple is significantly higher at $236.40, suggesting a disparity in pricing strategies or product mix.
3. Electronics category leads in revenue with $34,982.41, accounting for 43.4% of total revenue, followed by Home Appliances at 23.1%.
4. North America generated the highest revenue at $36,844.34, representing 45.7% of total revenue, while Asia contributed $22,455.45 (27.8%) and Europe $21,268.06 (26.5%).
5. The top product by revenue is the Canon EOS R5 Camera, generating $3,899.99 from a single unit sold, indicating a high-value item in the inventory.

=== SUMMARY ===
The analysis reveals strong revenue generation primarily from the Electronics category and North America region. There is a notable difference between average unit prices, indicating potential pricing strategy adjustments. The top products are high-value items, suggesting a focus on premium offerings could be beneficial.

=== RECOMMENDATIONS ===
1. Consider increasing marketing efforts for the Electronics category, which is the highest revenue generator, to further capitalize on its success.
2. Evaluate pricing strategies to align the average unit price simple and weighted, potentially adjusting prices to improve overall sales volume without sacrificing revenue.
3. Explore opportunities to expand product offerings in the North American region, as it shows the highest revenue contribution, while also assessing potential growth in the Asia and Europe markets.
```

---

## Results Analysis
See: `analysis.md`

---

## PowerBI Dashboard
A PowerBI dashboard (`csv-sales-analyzer.pbix`) is included for visual data exploration and analysis.

---

## Windsurf Workflows
The project includes custom workflows in `.windsurf/workflows/`:
- `insights.md`: Automated workflow for generating sales insights using MCP tools

---