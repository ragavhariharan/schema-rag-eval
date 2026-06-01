import asyncio
import nest_asyncio
import json
import re
import chromadb
import ollama
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy
)

# PROPER ASYNC IMPORTS (Fixes the 0% Deadlock)
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

# ─── 1. SETUP EVENT LOOP FOR PYTHON 3.14 ──────────────────────────────────────
nest_asyncio.apply()
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ─── 2. MONKEY-PATCH RAGAS RUNNER FOR PYTHON 3.14 COMPATIBILITY ───────────────
# Prevents background thread asyncio deadlocks by executing the event loop on the main thread.
import ragas.executor
class MainThreadRunner(ragas.executor.Runner):
    def start(self):
        self.run()
    def join(self, timeout=None):
        pass
    def run(self):
        old_loop = None
        try:
            old_loop = asyncio.get_event_loop()
        except RuntimeError:
            pass

        asyncio.set_event_loop(self.loop)

        import nest_asyncio
        nest_asyncio.apply(self.loop)

        # Re-create self.futures bound to self.loop
        self.futures = ragas.executor.as_completed(
            loop=self.loop,
            coros=[coro for coro, _ in self.jobs],
            max_workers=self.run_config.max_workers,
        )

        results = []
        try:
            results = self.loop.run_until_complete(self._aresults())
        finally:
            self.results = results
            self.loop.stop()
            if old_loop is not None:
                asyncio.set_event_loop(old_loop)
ragas.executor.Runner = MainThreadRunner

# ─── 3. MONKEY-PATCH LANGCHAIN LLM WRAPPER TO BE FULLY SYNCHRONOUS ────────────
# Avoids threadpool deadlocks inside loop.run_in_executor under Python 3.14.
import ragas.llms
from ragas.run_config import RunConfig, add_retry

async def patched_generate(
    self,
    prompt,
    n=1,
    temperature=1e-8,
    stop=None,
    callbacks=None,
    is_async=True,
):
    # Force the synchronous generate_text path directly (no run_in_executor)
    generate_text_with_retry = add_retry(self.generate_text, self.run_config)
    result = generate_text_with_retry(
        prompt=prompt,
        n=n,
        temperature=temperature,
        stop=stop,
        callbacks=callbacks,
    )
    return result
ragas.llms.LangchainLLMWrapper.generate = patched_generate

# ─── 4. INITIALIZE LLM AND EMBEDDINGS ─────────────────────────────────────────
print("⚙️  Initializing Local LLM and Embeddings...")
local_llm = ChatOllama(model="qwen2.5-coder", base_url="http://localhost:11434", num_ctx=32768)
local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ─── 5. CUSTOM CONTEXT PRECISION PROMPT FOR TEXT-TO-SQL ───────────────────────
# Replaces the default reading-comprehension prompt with one that understands
# that database schema chunks are useful context for SQL generation tasks.
from ragas.llms.prompt import Prompt

TEXT_TO_SQL_CONTEXT_PRECISION_PROMPT = Prompt(
    name="context_precision_for_text_to_sql",
    instruction="""Given a question, an answer, and a context chunk, verify if the context was useful in arriving at the given answer.

IMPORTANT: This is a TEXT-TO-SQL evaluation task.
- The "context" is a DATABASE SCHEMA CHUNK: it contains table names, column names, data types, and/or example SQL queries.
- The "answer" is a SQL query OR a natural language description of the SQL logic that answers the question.

A context chunk is USEFUL (verdict: 1) if it contains ANY of the following:
  - The table name referenced in the answer
  - One or more column names that appear in the answer's SELECT, WHERE, ORDER BY, or JOIN clauses
  - An example SQL query that demonstrates the same logical pattern (e.g., same table, similar filter or sort)

A context chunk is NOT useful (verdict: 0) ONLY if it references a completely different table AND has no columns relevant to the answer whatsoever.

Give verdict as "1" if useful and "0" if not with json output.""",
    examples=[
        {
            "question": "Which 12K 5µm lens has the least warping at the edges?",
            "context": "[Table: line_scan_lens_12k5u] Optical Attributes: focus_length_mm: Focal length | f_no_min: Minimum F-number | tv_distortion_percent: TV distortion value expressed as a percentage | fov_mm: Field of view in millimeters",
            "answer": "SELECT model_name, tv_distortion_percent FROM line_scan_lens_12k5u ORDER BY ABS(tv_distortion_percent) ASC LIMIT 1;",
            "verification": {"reason": "The context contains the 'line_scan_lens_12k5u' table and the 'tv_distortion_percent' column, which is the exact column used in the ORDER BY clause of the answer. This schema chunk is directly required to write the SQL answer.", "verdict": 1},
        },
        {
            "question": "Which 12K 5µm lens has the least warping at the edges?",
            "context": "[Table: line_scan_lens_16k5u] Query Type: Working Distance Search. SQL: SELECT model_name, wd_mm FROM line_scan_lens_16k5u WHERE wd_mm > 200;",
            "answer": "SELECT model_name, tv_distortion_percent FROM line_scan_lens_12k5u ORDER BY ABS(tv_distortion_percent) ASC LIMIT 1;",
            "verification": {"reason": "The context references 'line_scan_lens_16k5u', a completely different table from 'line_scan_lens_12k5u' used in the answer. No table or column overlap exists.", "verdict": 0},
        },
        {
            "question": "List the focal length and price of all 16K 3.5µm lenses.",
            "context": "[Table: line_scan_lens_16k3_5u] Dimension Attributes: list_price: Catalogue sales price | size_diameter_mm: Physical outer diameter | weight_g: Weight in grams",
            "answer": "SELECT model_name, focus_length_mm, list_price FROM line_scan_lens_16k3_5u;",
            "verification": {"reason": "The context contains 'line_scan_lens_16k3_5u' and the 'list_price' column, which appears in the SELECT clause of the answer. This makes the context directly useful.", "verdict": 1},
        },
    ],
    input_keys=["question", "context", "answer"],
    output_key="verification",
    output_type="json",
    language="english",
)

# Inject into the metric object — scoped only to context_precision
context_precision.context_precision_prompt = TEXT_TO_SQL_CONTEXT_PRECISION_PROMPT

# ─── 6. CONNECT TO CHROMADB ───────────────────────────────────────────────────
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="lens_schema_rag")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: DYNAMIC LLM HELPERS (replaces hardcoded regex + SQL_TRANSLATION_MAP)
# ═══════════════════════════════════════════════════════════════════════════════

OLLAMA_MODEL = "qwen2.5-coder"
OLLAMA_BASE_URL = "http://localhost:11434"

def llm_extract_filters(user_query: str) -> dict:
    """Dynamically extract ChromaDB metadata filters from a user query using the LLM.

    Uses Ollama's JSON mode for structured output. Returns a dict with keys
    matching ChromaDB metadata fields. Values are None for unidentified filters.
    """
    system_prompt = """You are a metadata filter extractor for a line scan lens catalog database.
Given a user's natural language query about lenses, extract the following metadata filters as JSON:

{
  "resolution_target": string or null (e.g. "4K", "8K", "12K", "16K" — extracted from mentions like "8K", "12k", "12K"),
  "pixel_pitch_um": number or null (e.g. 5.0, 7.0, 3.5 — extracted from mentions like "5u", "5µm", "5 micron", "3.5u"),
  "is_coaxial": true/false or null (true ONLY if the query explicitly mentions "coaxial"),
  "is_new_series": true/false or null (true ONLY if the query explicitly mentions "new series")
}

RULES:
- Return ONLY the JSON object, nothing else.
- Use null for any filter you cannot confidently extract from the query.
- "resolution_target" must always be uppercase with K suffix (e.g. "8K", not "8k").
- "pixel_pitch_um" must be a number (e.g. 3.5, not "3.5u").
- If the query mentions no specific resolution, pixel pitch, coaxial, or new series, return all nulls.
- Queries about general lens properties (e.g. "all lenses under 200g") should return all nulls."""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        format="json",
        options={"temperature": 0, "num_ctx": 32768}
    )

    try:
        parsed = json.loads(response["message"]["content"])
    except (json.JSONDecodeError, KeyError):
        # Fallback: no filters applied if LLM output is malformed
        return {"resolution_target": None, "pixel_pitch_um": None, "is_coaxial": None, "is_new_series": None}

    # Normalize the output — ensure all expected keys exist with correct types
    filters = {
        "resolution_target": None,
        "pixel_pitch_um": None,
        "is_coaxial": None,
        "is_new_series": None
    }

    if parsed.get("resolution_target") and isinstance(parsed["resolution_target"], str):
        val = parsed["resolution_target"].upper().replace(" ", "")
        if not val.endswith("K"):
            val += "K"
        filters["resolution_target"] = val

    if parsed.get("pixel_pitch_um") is not None:
        try:
            filters["pixel_pitch_um"] = float(parsed["pixel_pitch_um"])
        except (ValueError, TypeError):
            pass

    if isinstance(parsed.get("is_coaxial"), bool):
        filters["is_coaxial"] = parsed["is_coaxial"]

    if isinstance(parsed.get("is_new_series"), bool):
        filters["is_new_series"] = parsed["is_new_series"]

    return filters


def llm_translate_sql_to_nl(sql: str, question: str) -> str:
    """Dynamically translate a SQL query to a single English sentence using the LLM.

    Used to generate natural language ground truth for Ragas evaluation (which
    expects NL, not raw SQL, for Recall and Faithfulness grading).
    """
    system_prompt = """You are a SQL-to-English translator for a line scan lens catalog database.
Given a SQL query and the original user question, produce a single clear English sentence describing exactly what the SQL query does.

Focus on:
- Which table is being queried
- Which columns are selected
- Any WHERE filter conditions and their values
- Any ORDER BY and sort direction
- Any LIMIT clause

Return ONLY the English sentence, nothing else. Do not include any SQL, code, or explanation."""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\nSQL: {sql}"}
        ],
        options={"temperature": 0, "num_ctx": 32768}
    )

    result = response.get("message", {}).get("content", "").strip()
    # Fallback to raw SQL if LLM returns empty
    return result if result else sql


def extract_sql_from_text(text: str) -> str:
    """Extract clean SQL from an LLM response that may contain markdown fences."""
    sql_match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()
    generic_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip()
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: OBSERVABILITY — TERMINAL TRACE UI
# ═══════════════════════════════════════════════════════════════════════════════

TRACE_WIDTH = 80

def _box_line(text: str, prefix: str = "║  ", pad: bool = True) -> str:
    """Format a single line inside the box, truncating if needed."""
    max_content = TRACE_WIDTH - len(prefix) - 3  # 3 for trailing " ║"
    if len(text) > max_content:
        text = text[:max_content - 3] + "..."
    if pad:
        return f"{prefix}{text:<{max_content}} ║"
    return f"{prefix}{text} ║"

def print_generation_trace(idx: int, question: str, filters: dict, chunks: list[str],
                           generated_sql: str, ground_truth_nl: str):
    """Print a rich terminal trace for a single question during generation."""
    hr = "╠" + "═" * (TRACE_WIDTH - 2) + "╣"
    top = "╔" + "═" * (TRACE_WIDTH - 2) + "╗"
    bot = "╚" + "═" * (TRACE_WIDTH - 2) + "╝"

    lines = [top]
    lines.append(_box_line(f"Q{idx}: {question}", "║  "))
    lines.append(hr)

    # Filters
    lines.append(_box_line("FILTERS EXTRACTED (LLM):", "║  "))
    active_filters = {k: v for k, v in filters.items() if v is not None}
    if active_filters:
        for k, v in active_filters.items():
            lines.append(_box_line(f"  {k}: {v}", "║  "))
    else:
        lines.append(_box_line("  (none — semantic search only)", "║  "))
    lines.append(hr)

    # Retrieved Chunks
    lines.append(_box_line("RETRIEVED CHUNKS (Top 5):", "║  "))
    for rank, chunk in enumerate(chunks, 1):
        preview = chunk[:60].replace("\n", " ")
        lines.append(_box_line(f"  #{rank}: {preview}", "║  "))
    if not chunks:
        lines.append(_box_line("  (no chunks retrieved)", "║  "))
    lines.append(hr)

    # Generated SQL
    lines.append(_box_line("GENERATED SQL:", "║  "))
    for sql_line in generated_sql.strip().split("\n"):
        lines.append(_box_line(f"  {sql_line.strip()}", "║  "))
    lines.append(hr)

    # Ground Truth NL
    lines.append(_box_line("GROUND TRUTH (NL):", "║  "))
    # Word-wrap the NL translation at ~70 chars
    gt_words = ground_truth_nl.split()
    gt_line = ""
    for word in gt_words:
        if len(gt_line) + len(word) + 1 > 68:
            lines.append(_box_line(f"  {gt_line}", "║  "))
            gt_line = word
        else:
            gt_line = f"{gt_line} {word}".strip()
    if gt_line:
        lines.append(_box_line(f"  {gt_line}", "║  "))

    lines.append(bot)
    print("\n".join(lines), flush=True)


def print_grading_result(idx: int, question: str, scores: dict):
    """Print a compact scorecard line after grading a single question."""
    cp = scores.get("context_precision", float("nan"))
    cr = scores.get("context_recall", float("nan"))
    fa = scores.get("faithfulness", float("nan"))
    ar = scores.get("answer_relevancy", float("nan"))
    print(f"   ✅ Q{idx} │ Prec: {cp:.2f} │ Recall: {cr:.2f} │ Faith: {fa:.2f} │ Relev: {ar:.2f}",
          flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: PIPELINE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline(user_query: str):
    """Run the full RAG pipeline: extract filters → retrieve chunks → generate SQL."""
    # --- Dynamic LLM Filter Extraction ---
    filters = llm_extract_filters(user_query)

    search_params = {"query_texts": [user_query], "n_results": 5}

    and_conditions = []
    if filters.get("resolution_target"):
        and_conditions.append({"resolution_target": filters["resolution_target"]})
    if filters.get("pixel_pitch_um") is not None:
        and_conditions.append({"pixel_pitch_um": filters["pixel_pitch_um"]})
    if filters.get("is_coaxial") is True:
        and_conditions.append({"is_coaxial": True})
    if filters.get("is_new_series") is True:
        and_conditions.append({"is_new_series": True})

    if and_conditions:
        search_params["where"] = {"$and": and_conditions} if len(and_conditions) > 1 else and_conditions[0]

    results = collection.query(**search_params)
    contexts = results['documents'][0] if results['documents'] else []

    # --- SQL Generation ---
    system_prompt = f"""You are an expert PostgreSQL engineer. Write raw SQL.
RULES: Use ONLY the provided schema. Do not hallucinate columns. Always SELECT model_name.
SCHEMA: {"\n\n".join(contexts)}"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_query}],
        options={"num_ctx": 32768}
    )
    raw_response = response['message']['content']
    clean_sql = extract_sql_from_text(raw_response)
    return clean_sql, contexts, filters


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: DATASET GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_ragas_dataset():
    """Build the Ragas evaluation dataset with dynamic NL translation and observability."""
    with open("golden_dataset.json", "r") as f:
        golden_data = json.load(f)

    subset = golden_data
    data_dict = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    trace_data = []  # Collect per-question metadata for later CSV enrichment

    print("\n🚀 Generating pipeline outputs...\n")
    for idx, item in enumerate(subset, 1):
        # --- Run RAG pipeline ---
        sql, ctx, filters = run_pipeline(item['question'])

        # --- Dynamic NL ground truth translation ---
        gt_nl = llm_translate_sql_to_nl(item["expected_sql"], item["question"])

        data_dict["question"].append(item["question"])
        data_dict["answer"].append(sql)
        data_dict["contexts"].append(ctx)
        data_dict["ground_truth"].append(gt_nl)

        # --- Print terminal trace ---
        print_generation_trace(idx, item["question"], filters, ctx, sql, gt_nl)

        trace_data.append({
            "id": item["id"],
            "filters_extracted": json.dumps({k: v for k, v in filters.items() if v is not None}),
            "num_chunks": len(ctx),
            "generated_sql": sql,
            "ground_truth_nl": gt_nl
        })

    return Dataset.from_dict(data_dict), trace_data


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: MAIN EVALUATION LOOP WITH OBSERVABILITY
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    dataset, trace_data = generate_ragas_dataset()

    print("\n🧠 Grading...\n")
    results = []

    for i in range(len(dataset)):
        row = dataset[i]
        single_ds = Dataset.from_dict({
            "question": [row["question"]],
            "answer": [row["answer"]],
            "contexts": [row["contexts"]],
            "ground_truth": [row["ground_truth"]]
        })

        score = evaluate(
            dataset=single_ds,
            metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
            llm=local_llm,
            embeddings=local_embeddings,
            raise_exceptions=False,
            is_async=False,
            run_config=RunConfig(max_workers=-1)
        )

        score_df = score.to_pandas()
        results.append(score_df)

        # --- Print per-question grading result ---
        score_row = score_df.iloc[0].to_dict()
        print_grading_result(i + 1, row["question"], score_row)

    # ─── FINAL SCORECARD ──────────────────────────────────────────────────────
    final_df = pd.concat(results, ignore_index=True)

    # Enrich with trace metadata
    for idx, trace in enumerate(trace_data):
        for key, val in trace.items():
            final_df.loc[idx, key] = val

    # ─── CSV EXPORT ───────────────────────────────────────────────────────────
    csv_path = "detailed_evaluation_trace.csv"
    final_df.to_csv(csv_path, index=False)

    print(f"\n📁 Detailed trace exported to: {csv_path}")
    print("\n" + "=" * 50)
    print("📊 FINAL SCORECARD:")
    print(f"   Context Precision : {final_df['context_precision'].mean():.2f}")
    print(f"   Context Recall    : {final_df['context_recall'].mean():.2f}")
    print(f"   Faithfulness      : {final_df['faithfulness'].mean():.2f}")
    print(f"   Answer Relevancy  : {final_df['answer_relevancy'].mean():.2f}")
    print("=" * 50)