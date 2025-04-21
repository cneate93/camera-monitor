# Use an official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy only necessary files first (to cache dependencies)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the Flask port
EXPOSE 5000

# Run the app
CMD ["python", "run.py"]