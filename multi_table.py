"""
multi_table.py
═════════════════════════════════════════════════════════════════════════════════
Deterministic multi-table UNION expander (Phase 2).

The local LLM reliably writes a correct SINGLE-table query, but not a correct
multi-table UNION. Since this catalog is "parallel tables, no joins" (every table
keyed on model_name, no foreign keys), any multi-table question is structurally
"run the same single-table query against several tables and stack the results".

So we let the model write the single-table query, then expand it here:
  1. Parse the single-table SELECT.
  2. Find every column it references.
  3. From the candidate tables, keep only those whose schema (per the registry)
     contains ALL of those columns — this is what makes it general and prevents
     "column does not exist" errors (e.g. accessory tables with no list_price are
     skipped automatically; nothing table- or column-specific is hardcoded).
  4. Replicate the SELECT across the survivors, combined with UNION ALL.
  5. If the query is a superlative (ORDER BY / LIMIT), move that to an outer query
     so it applies across the combined set, not per-table.

Returns the original SQL unchanged whenever expansion does not cleanly apply
(already a UNION, has joins / GROUP BY / aggregates, SELECT *, only one table
qualifies, etc.) — so it never makes a query worse.
═════════════════════════════════════════════════════════════════════════════════
"""
import sqlglot
from sqlglot import exp


def _referenced_columns(ast: exp.Expression) -> set:
    """All column names referenced anywhere in the query (select, where, order)."""
    return {
        c.name.lower()
        for c in ast.find_all(exp.Column)
        if c.name and c.name != "*"
    }


def expand_to_tables(sql: str, candidate_tables: list, registry: dict) -> str:
    """Replicate a single-table SELECT across candidate tables that share its
    columns, combined with UNION ALL. See module docstring for the contract.

    Returns the expanded SQL, or the original `sql` if expansion doesn't apply.
    """
    try:
        ast = sqlglot.parse_one(sql, read="postgres")
    except Exception:
        return sql

    # Only plain single-table SELECTs are expandable.
    if not isinstance(ast, exp.Select):
        return sql
    if ast.find(exp.Union) or ast.find(exp.Group) or ast.find(exp.AggFunc) or ast.find(exp.Join):
        return sql
    if any(isinstance(e, exp.Star) for e in ast.expressions):
        return sql

    tables = list(ast.find_all(exp.Table))
    if len(tables) != 1:
        return sql
    base_table = tables[0].name.lower()

    referenced = _referenced_columns(ast)
    if not referenced:
        return sql

    # Output columns (names/aliases) the outer wrapper will select.
    output_cols = [e.alias_or_name for e in ast.expressions]
    out_names = {o.lower() for o in output_cols}

    order = ast.args.get("order")
    limit = ast.args.get("limit")

    # Don't expand if ORDER BY references a column the SELECT doesn't expose —
    # the outer wrapper wouldn't be able to see it.
    if order:
        order_cols = {c.name.lower() for c in order.find_all(exp.Column)}
        if not order_cols <= out_names:
            return sql

    # Keep only candidate tables whose schema contains ALL referenced columns.
    qualifying = [
        t for t in candidate_tables
        if referenced <= set(registry.get(t, []))
    ]
    # Base table first, then the rest; dedupe; preserve order.
    ordered = []
    for t in [base_table] + qualifying:
        if t in qualifying and t not in ordered:
            ordered.append(t)
    if len(ordered) <= 1:
        return sql  # nothing to combine

    select_list = ", ".join(e.sql(dialect="postgres") for e in ast.expressions)
    where = ast.args.get("where")
    where_sql = where.sql(dialect="postgres") if where else ""

    parts = []
    for t in ordered:
        part = f"SELECT {select_list} FROM {t}"
        if where_sql:
            part += f" {where_sql}"
        parts.append(part)
    union_sql = " UNION ALL ".join(parts)

    if order or limit:
        outer = f"SELECT {', '.join(output_cols)} FROM ({union_sql}) AS combined"
        if order:
            outer += " " + order.sql(dialect="postgres")
        if limit:
            outer += " " + limit.sql(dialect="postgres")
        return outer + ";"
    return union_sql + ";"
