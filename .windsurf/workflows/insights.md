# /insights
Generate insights from the csv-analyzer MCP by chaining tools: compute KPIs → generate OpenAI insights.

## Steps
1. Use the user's last message as the analysis question.
2. Use filters = {} unless the user explicitly provides filters JSON.
3. Do NOT call "list resources". Go directly to tools.

4. Call KPI tool:
<compute_sales_kpis>{"filters": {}}</compute_sales_kpis>

5. Immediately call OpenAI insights tool:
- Set `kpis` to the FULL output returned from step 4 (exactly as returned).
- Set `question` to the user's question.

<openai_generate_insights>{
  "kpis": "__USE_OUTPUT_FROM_STEP_4__",
  "question": "__USE_USER_QUESTION__"
}</openai_generate_insights>

6. Present final answer in this format:
=== INSIGHTS ===
- 3–7 bullets with numbers/percentages
=== SUMMARY ===
- 2–4 lines
=== RECOMMENDATIONS ===
- 3–5 actionable recommendations
