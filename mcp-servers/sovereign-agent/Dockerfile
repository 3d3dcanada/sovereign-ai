FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install mcp pydantic

# Copy agent code
COPY agent.py /app/agent.py

# Create directories
RUN mkdir -p /app/logs /workspace

EXPOSE 8501

CMD ["python", "agent.py"]
