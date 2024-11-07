
# Declare the build argument before any FROM instructions
FROM python:3.12-alpine AS base

WORKDIR /usr/src/FIT

# Copy the requirements.txt file
COPY requirements.txt .

# Create the logs/docker folder unconditionally
RUN mkdir -p /usr/src/FIT/logs/docker

# Log the output of apk update, apk upgrade, and pip install to the logs/docker folder
RUN apk update 2>&1 | tee /usr/src/FIT/logs/docker/apk_update.log && \
    apk add --no-cache openssl=3.3.2-r1 2>&1 | tee /usr/src/FIT/logs/docker/openssl_upgrade.log && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt 2>&1 | tee /usr/src/FIT/logs/docker/pip_install.log

FROM base AS api

WORKDIR /usr/src/FIT

# Copy application files
COPY API /usr/src/FIT/API
COPY config /usr/src/FIT/config
COPY data/FIT.db /usr/src/FIT/data/FIT.db
COPY tests /usr/src/FIT/tests
COPY docker/start_server.sh /usr/src/FIT/start_server.sh
COPY docker/run_tests.sh /usr/src/FIT/run_tests.sh

# Ensure the logs folder exists in this stage as well
RUN mkdir -p /usr/src/FIT/logs

# Make scripts executable
RUN chmod +x /usr/src/FIT/start_server.sh /usr/src/FIT/run_tests.sh

# Expose the application port
EXPOSE 80

# Set the default command to start the server
CMD ["./start_server.sh"]
