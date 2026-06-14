FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8501') + '/_stcore/health')"

ENTRYPOINT streamlit run streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
