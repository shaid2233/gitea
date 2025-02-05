# Step 1: Use an official Python base image
FROM python:3.9-slim

# Step 2: Set the working directory inside the container
WORKDIR /usr/src/app

# Step 3: Copy requirements file to the working directory
COPY requirements.txt ./

# Step 4: Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the rest of the application source code to the working directory
COPY . .



# Step 6: Set environment variables
ENV DB_HOST=localhost
ENV DB_PORT=3306
ENV DB_USER=root
ENV DB_PASSWORD=123456



# Step 6: Expose the port the app will run on
EXPOSE 5000

# Step 7: Define the command to run the application
CMD ["python", "main.py"]