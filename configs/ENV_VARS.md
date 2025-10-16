# Environment Variables

| Name | Purpose | Required | Default | Example |
|------|---------|----------|---------|---------|
| APP_STAGE | Stage selector | yes | - | local|ci|staging|prod |
| POLICY_MODE | Tool gating strictness | no | strict | strict|permissive |
| LLM_PROVIDER | LLM backend | yes | - | anthropic|openai |
| OPENAI_API_KEY | OpenAI key | req if provider=openai | - | sk-*** |
| ANTHROPIC_API_KEY | Anthropic key | req if provider=anthropic | - | sk-ant-*** |
| LLM_MODEL | Chat model ID | yes | - | anthropic.claude-3-haiku |
| EMBEDDINGS_MODEL | Embedding model ID | yes | - | titan-embed-text-v1 |
| VECTOR_STORE | Vector backend | yes | chroma | pgvector|chroma|faiss |
| VECTOR_DB_URL | Vector DB conn string | req if store=pgvector | - | postgres://user:pass@host:5432/db |
| CACHE_URL | Cache conn string | no | - | redis://host:6379 |
| MCP_SERVERS | Tool registry (comma-separated) | yes | - | rag.retrieve,papers.search,... |
| MCP_REGISTRY_JSON | Tool→URL mapping (JSON) | no | - | {"rag.retrieve":"http://localhost:7001","papers.search":"http://localhost:7002","papers.fetch":"http://localhost:7002","notes.read":"http://localhost:7003","notes.write":"http://localhost:7003","db.query":"http://localhost:7004","ingest.upload":"http://localhost:7005","ingest.extract":"http://localhost:7005","ingest.embed":"http://localhost:7005"} |

Guidelines:
- Secrets are never committed; inject via env/secret manager.
- Validate presence and format at process start; fail fast on required fields.
- Redact secrets in logs; lint CI configs to prevent accidental echo.
