# Python Anti-Patterns & Best Practices

## Common Anti-Patterns to Avoid

### 1. **Mutable Default Arguments**
❌ `def process(items=[]): items.append("new"); return items`
✅ `def process(items=None): items = items or []; items.append("new"); return items`

### 2. **Using `pass` in Production**
❌ `def get_logs(date): pass  # TODO`
✅ `def get_logs(date): raise NotImplementedError("Pending")`

### 3. **Bare `except` Clauses**
❌ `try: risky(); except: pass`
✅ `try: risky(); except SpecificError as e: logger.error(f"Failed: {e}")`

### 4. **Pydantic v2 Migration**
❌ `metrics_data.dict()` (deprecated)
✅ `metrics_data.model_dump()`

### 5. **Missing Type Hints**
❌ `def process(data): return data.items()`
✅ `def process(data: Dict[str, Any]) -> List[Any]: return list(data.items())`

### 6. **Hardcoding Configuration**
❌ `api_key = "secret123"`
✅ `api_key = settings.toggl_api_token` (from environment)

### 7. **None Comparison**
❌ `if value == None:`
✅ `if value is None:`

### 8. **Wildcard Imports**
❌ `from app.services import *`
✅ `from app.services import analysis_service`

### 9. **Indentation**
* No trailing whitespaces.
* No unnecessary indentation after new line.

### 10. **Unnecessary Documentation/Comments**
❌ `# Sum up all durations (duration is in seconds)`
❌ `total_duration_seconds = sum(entry.duration for entry in time_entries)`
✅ `total_duration_seconds = sum(entry.duration for entry in time_entries)`
* Avoid comments that simply restate what the code already clearly expresses
* Code should be self-documenting through clear variable names and structure
* Only add comments when they explain "why" not "what"

### 11. **Using PascalCase for Model Fields**
❌ `class CreatePlanRequest(BaseModel): Prompt: str; StartDate: str`
✅ `class CreatePlanRequest(BaseModel): prompt: str; start_date: str`
* Use snake_case for all field names in Pydantic models (Python convention)
* This project uses Python, so follow Python naming conventions

## Best Practices

- **Pydantic models** for all request/response validation
- **Type hints** everywhere for IDE support
- **One responsibility** per service
- **Raise exceptions** instead of error dictionaries
- **Use async/await** for I/O operations
- **Log operations** using Python's logging module
- **Environment variables** for all configuration
- **Keep routes thin** - delegate to services immediately
