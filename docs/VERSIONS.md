# Version Matrix

| Component | Version / Constraint |
|-----------|----------------------|
| Python | 3.12.x |
| FastAPI / ASGI | latest stable |
| LangGraph | latest stable |
| LangChain | latest stable |
| CrewAI | latest stable |
| AutoGen | latest stable |
| Vector store | pgvector (prod), FAISS/Chroma (local/CI) |
| Cache | Redis (staging/prod), SQLite (local/CI) |
| Telemetry | OpenTelemetry API/SDK latest stable |

Notes:
- Pin exact versions during implementation to ensure reproducibility.
- Track breaking changes in CHANGELOG.
