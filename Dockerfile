# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --default-timeout is added to prevent timeout errors on slow networks
# --no-cache-dir disables the pip cache, which reduces the image size
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Copy the rest of the application's code from your local machine to the container
COPY . .

# Make port 8501 available to the world outside this container
# This is the default port Streamlit runs on
EXPOSE 8501

# Define the command to run your app using streamlit
# The --server.port and --server.address options are best practices for containerized apps
CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
