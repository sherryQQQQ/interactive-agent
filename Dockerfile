FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY interactive_agent/ interactive_agent/
COPY graphrag/ graphrag/
RUN pip install --no-cache-dir .
ENV LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false MEDICAL_RAG_LANGSMITH_TRACING=false PYTHONUNBUFFERED=1
ENTRYPOINT ["interactive-agent"]
CMD ["catalog"]
