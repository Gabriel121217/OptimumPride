FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Copy the .env file into the container
COPY .env /app/.env

# Install any necessary Python packages specified in requirements.txt
# Uncomment if you have a requirements.txt file:
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Run OrionPax.py when the container launches
CMD ["python3", "OrionPax.py"]
