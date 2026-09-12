# Official Playwright Python image — browser আলাদা install করতে হবে না
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Dependencies install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# সব code copy
COPY . .

# Downloads folder তৈরি করো
RUN mkdir -p /tmp/downloads

# Bot চালু করো
CMD ["python", "main.py"]
