# Start from an official slim Python image (small, official, reproducible).
FROM python:3.12-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy just requirements first, then install — this caches the install layer
# so rebuilds are fast when only your code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the project code into the container.
COPY . .

# The command that runs when the container starts.
CMD ["python", "src/email_agent.py", "auto"]
