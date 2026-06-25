FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application.
COPY . .

# Generate sample data at image build time so the container can run
# main.py immediately without an extra setup step.
RUN python data/sample_data.py

CMD ["python", "main.py"]
