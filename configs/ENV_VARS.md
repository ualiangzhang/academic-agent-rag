# Environment Variables

| Name | Purpose | Example |
|------|---------|---------|
| APP_STAGE | Stage selector | local|ci|staging|prod |
| POLICY_MODE | Tool gating strictness | strict |
| LLM_PROVIDER | LLM backend | anthropic|openai |
| OPENAI_API_KEY | OpenAI key | sk-*** |
| ANTHROPIC_API_KEY | Anthropic key | sk-ant-*** |
| LLM_MODEL | Chat model ID | anthropic.claude-3-haiku |
| EMBEDDINGS_MODEL | Embedding model ID | titan-embed-text-v1 |
| VECTOR_STORE | Vector backend | pgvector|chroma|faiss |
| VECTOR_DB_URL | Vector DB conn string | postgres://user:pass@host:5432/db |
| CACHE_URL | Cache conn string | redis://host:6379 |
| MCP_SERVERS | Comma-separated tool registry | rag.retrieve,papers.search,... |

Guidelines:
- Secrets are never committed; inject via env/secret manager.
- Validate presence and format at process start.
