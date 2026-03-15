# Multi-process docker container for both components
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt backend/
COPY frontend/requirements.txt frontend/

RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r frontend/requirements.txt

COPY . .

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Shell script to run both
RUN echo '#!/bin/sh\n\
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &\n\
BACKEND_URL="http://localhost:8000" streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0\n\
wait -n\n\
exit $?' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
