import json
# pyrefly: ignore [missing-import]
import sqlglot
# pyrefly: ignore [missing-import]
from sqlglot import exp
from pydantic import BaseModel

class ValidationResult(BaseModel):
    is_valid: bool
    read_only: bool
    tables_valid: bool
    columns_valid: bool
    reason: str

class SQLValidator:
    def __init__(self, schema_registry_path: str = "schema_registry.json"):
        with open(schema_registry_path, "r") as f:
            self.schema_registry = json.load(f)
            
        # Create a fast lookup for table existence
        self.valid_tables = set(self.schema_registry.keys())

    def validate(self, sql: str) -> ValidationResult:
        # 1. Syntax Check
        try:
            # Parse using Postgres dialect
            parsed = sqlglot.parse(sql, read="postgres")
            if not parsed or not parsed[0]:
                return self._fail("Syntax Check", "Could not parse SQL")
            ast = parsed[0]
        except (sqlglot.errors.ParseError, sqlglot.errors.TokenError) as e:
            return self._fail("Syntax Check", f"Invalid PostgreSQL syntax: {str(e)}")

        # 2. Read-Only Enforcement
        forbidden_nodes = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Alter,
            exp.Command,
            exp.TruncateTable
        )
        
        # ast.walk() yields the node directly
        for node in ast.walk():
            if isinstance(node, forbidden_nodes):
                return self._fail("Read-Only", f"Forbidden operation detected: {type(node).__name__}")

        # 3. Table Grounding
        extracted_tables = set()
        for node in ast.find_all(exp.Table):
            table_name = node.name.lower()
            extracted_tables.add(table_name)
            
        # Filter out CTE aliases if any
        ctes = set()
        for cte in ast.find_all(exp.CTE):
            ctes.add(cte.alias.lower())
            
        final_tables = extracted_tables - ctes
            
        for t in final_tables:
            if t not in self.valid_tables:
                return self._fail("Table Grounding", f"Unknown table '{t}'")

        # 4. Column Grounding
        valid_columns_for_query = set()
        for t in final_tables:
            valid_columns_for_query.update(self.schema_registry[t])
            
        # Collect aliases defined in the query to avoid failing on them
        for node in ast.find_all(exp.Alias):
            alias_name = node.alias.lower()
            if alias_name:
                valid_columns_for_query.add(alias_name)
            
        for node in ast.find_all(exp.Column):
            col_name = node.name.lower()
            
            if col_name == "*":
                continue
                
            if col_name not in valid_columns_for_query:
                # If there are no tables queried, give a specific message
                if not final_tables:
                    return self._fail("Column Grounding", f"Unknown column '{col_name}' (No tables queried)")
                return self._fail("Column Grounding", f"Unknown column '{col_name}' in referenced tables")

        # All checks passed!
        return ValidationResult(
            is_valid=True,
            read_only=True,
            tables_valid=True,
            columns_valid=True,
            reason="Validation Passed"
        )
        
    def _fail(self, stage: str, reason: str) -> ValidationResult:
        return ValidationResult(
            is_valid=False,
            read_only=(stage != "Read-Only"),
            tables_valid=(stage != "Table Grounding"),
            columns_valid=(stage != "Column Grounding"),
            reason=f"Validation Failed [{stage}]: {reason}"
        )
