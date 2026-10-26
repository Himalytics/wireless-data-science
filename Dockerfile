FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN python -m pip install --no-cache-dir -r requirements.lock.txt
COPY . .
RUN python -m pip install --no-deps .
ENTRYPOINT ["wireless-de"]
CMD ["run"]
