FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY mangoagent mangoagent
COPY backend backend
COPY dashboard dashboard
COPY results/dqn_weights.npz results/dqn_weights.npz
ENV DB_PATH=/data/orchard.db
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
