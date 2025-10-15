# MCP Tools and Responsibilities (Baseline)

- rag.retrieve: semantic retrieval over the project corpus, return chunks with citations and scores.
- papers.search: internet discovery across arXiv/Crossref/Semantic Scholar; return metadata and links.
- papers.fetch: fetch and parse PDFs; output text and extracted metadata.
- notes.read: read persisted research notes by key/query.
- notes.write: write or update notes with metadata and versioning.
- db.query: SQL over Postgres/pgvector for advanced filtering and joins.
