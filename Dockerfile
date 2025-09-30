# Step 1: Start with an official lightweight Python base image
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy our "shopping list" into the container
COPY requirements.txt .

# Step 4: Install all the libraries from our list
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy our application code into the container
COPY main.py .

# Step 6: Set the default command to run when the container starts
ENTRYPOINT ["python", "main.py"]