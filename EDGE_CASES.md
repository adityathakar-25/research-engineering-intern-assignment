# Backend API Edge Cases & Hardening

This document tracks the explicit input boundaries and failure management capabilities introduced into the NarrativeTrace FastAPI layer to prevent application crashes and prevent sensitive stacktrace exposures.

## 1. Global Protective Catch-All
* **Implementation:** `main.py` explicitly attaches a global `@app.exception_handler(Exception)` intercept.
* **Behaviour:** Any unhandled internal code crash dynamically transforms into a secure JSON packet `{"error": "stringified_message", "code": 500}`. Tracebacks are never piped to the HTTP response.

## 2. Tested Input Validations

| Case | API Route | Test Pattern | Expected & Actual Behavior |
|------|-----------|--------------|----------------------------|
| **Empty Query String** | `GET /api/timeseries?query=` | `query=""` | Bypasses length validation internally since Pydantic minimum length is set to `0`. Route actively catches `len(query) < 2` explicitly tossing `HTTPException(400) "Query must be at least 2 characters"`. Gracefully denied. |
| **Short Query String** | `GET /api/timeseries?query=a` | `query="a"` | Same path as empty string. `len(query.strip()) < 2` safely rejects the request with a handled `400 Bad Request` instead of executing heavy DataFrame logic. |
| **Non-English Tokens** | `POST /api/search` | `{"query":"вакцина", "limit":20}` | Semantic model encodes Russian native inputs perfectly against ChromaDB vector space. Model implicitly supports multi-lingual tokens; limits pass properly scoped against `limit: le=200` configurations yielding functional arrays. |
| **Extreme Date Ranges** | `GET /api/timeseries` | `start=2000-01-01&end=2000-06-01` | Dates map properly via `fromisoformat`. Even though Data is naturally limited between `2022-01-01` to `...`, the filter parses mathematically, mapping an empty result space avoiding system `ValueError` exceptions by wrapping formats in structured `try/except` handlers throwing Clean `400` formats. |
| **Over-scaled Clustering Limits** | `GET /api/clusters` | `n_clusters=50` | Supported by Pydantic native arguments `le=50`. Backending logic checks total items vs clusters; automatically dynamically re-scales outputs passing functional boundaries via internal `capped_n_clusters` equations returning warnings inside the JSON payload safely! |

## 3. Frontend ErrorBoundary Protective Wrappers
If edge constraints fail over or network failures cause data to drop entirely, wrapping each widget dynamically inside native `<ErrorBoundary>` logic intercepts the crash avoiding total DOM tear-downs, dropping fallback "Something went wrong loading this section." elements over the respective chart only.
