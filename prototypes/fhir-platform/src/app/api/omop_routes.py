"""OMOP AI chat endpoint — natural language → SQL → results."""

import json
import logging
from typing import Any, Literal

import anthropic
import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# OMOP schema context for the LLM
# ---------------------------------------------------------------------------

OMOP_SCHEMA = """
You are an expert data analyst working with an OMOP CDM v5.4 PostgreSQL database
populated from Synthea synthetic patient data.

CRITICAL RULES — you MUST follow these without exception:
1. NEVER select condition_source_value, drug_source_value, measurement_source_value,
   or observation_source_value as the display name. These are raw numeric codes (SNOMED,
   RxNorm, LOINC) that are meaningless to users.
2. ALWAYS JOIN the concept table to get concept_name whenever you display a condition,
   drug, measurement, or observation. The concept table contains the human-readable label.
3. Every query that touches condition_occurrence MUST join concept on
   condition_concept_id = concept.concept_id and SELECT concept.concept_name.
4. Every query that touches drug_exposure MUST join concept on
   drug_concept_id = concept.concept_id and SELECT concept.concept_name.
5. Every query that touches measurement MUST join concept on
   measurement_concept_id = concept.concept_id and SELECT concept.concept_name.
6. Every query that touches observation MUST join concept on
   observation_concept_id = concept.concept_id and SELECT concept.concept_name.

Tables and key columns:

concept
  concept_id (int PK), concept_name (text) — human-readable label,
  domain_id (text) — 'Condition'/'Drug'/'Measurement'/'Observation',
  vocabulary_id (text) — 'SNOMED'/'RxNorm'/'LOINC'/'ICD10CM',
  concept_code (text) — raw source code (SNOMED/LOINC/RxNorm)

person
  person_id (int PK), gender_concept_id (int),
  year_of_birth (int), month_of_birth (int), day_of_birth (int),
  race_concept_id (int), ethnicity_concept_id (int),
  person_source_value (text) — original FHIR patient UUID,
  gender_source_value (text) — 'male' or 'female'

observation_period
  observation_period_id (int PK), person_id (int FK → person),
  observation_period_start_date (date), observation_period_end_date (date),
  period_type_concept_id (int, always 32817)

visit_occurrence
  visit_occurrence_id (int PK), person_id (int FK → person),
  visit_concept_id (int, always 0 — not populated, do NOT join concept or filter on this column),
  visit_start_date (date), visit_end_date (date),
  visit_type_concept_id (int, always 32817),
  visit_source_value (text) — FHIR encounter UUID

condition_occurrence
  condition_occurrence_id (int PK), person_id (int FK → person),
  condition_concept_id (int FK → concept.concept_id),
  condition_start_date (date), condition_end_date (date nullable),
  condition_type_concept_id (int, always 32817),
  condition_source_value (text) — raw SNOMED CT code (DO NOT display to users),
  visit_occurrence_id (int FK → visit_occurrence, nullable)

drug_exposure
  drug_exposure_id (int PK), person_id (int FK → person),
  drug_concept_id (int FK → concept.concept_id),
  drug_exposure_start_date (date), drug_exposure_end_date (date nullable),
  drug_type_concept_id (int, always 32817),
  drug_source_value (text) — raw RxNorm code (DO NOT display to users),
  visit_occurrence_id (int FK → visit_occurrence, nullable)

measurement
  measurement_id (int PK), person_id (int FK → person),
  measurement_concept_id (int FK → concept.concept_id),
  measurement_date (date),
  measurement_type_concept_id (int, always 32817),
  value_as_number (float nullable) — the numeric result,
  unit_concept_id (int, always 0),
  measurement_source_value (text) — raw LOINC code (DO NOT display to users),
  visit_occurrence_id (int FK → visit_occurrence, nullable)

observation
  observation_id (int PK), person_id (int FK → person),
  observation_concept_id (int FK → concept.concept_id),
  observation_date (date),
  observation_type_concept_id (int, always 32817),
  value_as_string (text nullable),
  observation_source_value (text) — raw LOINC code (DO NOT display to users),
  visit_occurrence_id (int FK → visit_occurrence, nullable)

REQUIRED JOIN pattern — top conditions example:
  SELECT c.concept_name AS condition_name, COUNT(*) AS n
  FROM condition_occurrence co
  JOIN concept c ON co.condition_concept_id = c.concept_id
  GROUP BY c.concept_name ORDER BY n DESC LIMIT 10;

REQUIRED JOIN pattern — top drugs example:
  SELECT c.concept_name AS drug_name, COUNT(*) AS n
  FROM drug_exposure de
  JOIN concept c ON de.drug_concept_id = c.concept_id
  GROUP BY c.concept_name ORDER BY n DESC LIMIT 10;

EXCLUDED CONDITIONS (always filter these out from condition_occurrence queries):
  'Full-time employment (finding)', 'Part-time employment (finding)'
Apply this as: WHERE c.concept_name NOT IN ('Full-time employment (finding)', 'Part-time employment (finding)')
whenever querying condition_occurrence joined to concept.

CURRENT USER: person_id = 3
When the user refers to themselves ("my conditions", "my medications", "my visits", "I", "me"),
filter by WHERE person_id = 3.

Generate a single read-only PostgreSQL SELECT query. Return ONLY the raw SQL
with no markdown, no explanation, no code fences. The query must be safe and
read-only (no INSERT, UPDATE, DELETE, DROP, TRUNCATE, etc.).
Limit results to 200 rows unless the user asks for an aggregate/count.
"""


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    question: str
    history: list[dict[str, str]] = []  # [{role: "user"|"assistant", content: str}]


class ChartSpec(BaseModel):
    type: Literal["bar", "line", "pie"]
    label_column: str
    value_column: str
    title: str


class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    results: list[dict[str, Any]]
    row_count: int
    insight: str
    chart_spec: ChartSpec | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_sql(question: str, history: list[dict[str, str]]) -> str:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    messages = list(history) + [{"role": "user", "content": question}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=OMOP_SCHEMA,
        messages=messages,
    )
    return response.content[0].text.strip()


def _generate_insight(
    question: str,
    sql: str,
    columns: list[str],
    results: list[dict[str, Any]],
    row_count: int,
) -> tuple[str, "ChartSpec | None"]:
    """Generate insight text and optional chart spec from query results."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    sample = results[:50]
    data_block = f"Columns: {columns}\nRows ({min(row_count, 50)} of {row_count} shown):\n"
    for row in sample:
        data_block += str(row) + "\n"

    prompt = (
        f"The user asked: {question!r}\n\n"
        f"SQL executed:\n{sql}\n\n"
        f"Results:\n{data_block}\n"
        "Respond with a single JSON object — no markdown, no code fences — exactly like this:\n"
        '{"insight": "<1-3 sentence interpretation for a clinical analyst>", '
        '"chart": {"type": "bar"|"line"|"pie", "label_column": "<exact column name>", '
        '"value_column": "<exact numeric column name>", "title": "<short chart title>"} | null}\n\n'
        "Rules for 'chart':\n"
        "- null if data is not suitable for a chart (free-text results, single row, no clear numeric column)\n"
        "- 'bar' when there is a category column and a count/aggregate numeric column\n"
        "- 'line' when the label column contains dates or years and the value is numeric\n"
        "- 'pie' when there are 2-8 category rows representing proportions or shares\n"
        f"- label_column and value_column MUST be exact names from this list: {columns}\n"
        "- Do not invent column names."
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    block = response.content[0]
    raw_text: str = str(block.text).strip() if hasattr(block, "text") else ""  # type: ignore[union-attr]

    # Strip markdown code fences if the model ignored our instructions
    stripped: str = raw_text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]  # drop opening fence line
        stripped = stripped.rsplit("```", 1)[0].strip()  # drop closing fence

    try:
        parsed = json.loads(stripped)
        insight_text = parsed.get("insight", "")
        chart_raw = parsed.get("chart")
        chart_spec = ChartSpec(**chart_raw) if chart_raw else None
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        insight_text = raw_text
        chart_spec = None

    return insight_text, chart_spec


def _execute_sql(sql: str) -> tuple[list[str], list[dict[str, Any]]]:
    if not settings.omop_database_url:
        raise HTTPException(status_code=500, detail="OMOP_DATABASE_URL is not configured")

    # Reject obviously unsafe statements
    sql_upper = sql.upper()
    for keyword in ("INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT"):
        if keyword in sql_upper:
            raise HTTPException(status_code=400, detail=f"Unsafe SQL keyword detected: {keyword}")

    conn = psycopg2.connect(settings.omop_database_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            results = [dict(row) for row in rows]
            return columns, results
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("/query", response_model=QueryResponse)
def query_omop(req: QueryRequest):
    """Generate SQL from a natural language question and execute it against the OMOP DB."""
    logger.info("OMOP query: %s", req.question)

    sql = _generate_sql(req.question, req.history)
    logger.info("Generated SQL: %s", sql)

    try:
        columns, results = _execute_sql(sql)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("SQL execution failed: %s\nSQL: %s", exc, sql)
        raise HTTPException(status_code=422, detail=f"SQL execution failed: {exc}\n\nGenerated SQL:\n{sql}")

    row_count = len(results)
    insight, chart_spec = _generate_insight(req.question, sql, columns, results, row_count)

    if chart_spec is not None:
        col_set = set(columns)
        if chart_spec.label_column not in col_set or chart_spec.value_column not in col_set:
            logger.warning(
                "Chart spec rejected — hallucinated columns: label=%s value=%s actual=%s",
                chart_spec.label_column, chart_spec.value_column, columns,
            )
            chart_spec = None

    return QueryResponse(
        question=req.question,
        sql=sql,
        columns=columns,
        results=results,
        row_count=row_count,
        insight=insight,
        chart_spec=chart_spec,
    )
