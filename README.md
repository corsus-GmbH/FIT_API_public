
## Setting Up the Docker Container

This guide walks you through setting up the Docker container for `FIT-API`, from the basic setup to advanced configurations for log management.

### Prerequisites

To follow these instructions, ensure that Docker is installed on your system. Installation steps vary by operating system, so consult the [Docker Documentation](https://docs.docker.com/get-docker/) for instructions specific to your OS.

Additionally, make sure you have Git installed. You can download it from the [Git Downloads page](https://git-scm.com/downloads), which includes options for Windows, macOS, and Linux.

### Getting the Git Repository

To get started, you can obtain the Git repository for `FIT-API` using either the command line or through your web browser. Make sure you navigate to the directory where you want the repository stored before proceeding.

#### Option 1: Using the Command Line

1. **Navigate to the directory** where you want the repository to be stored. For example:

   ```bash
   cd /path/to/your/desired/folder
   ```

   Replace `/path/to/your/desired/folder` with the path to the folder where you want to keep the repository.

2. **Clone the repository** using Git:

   ```bash
   git clone TODO: REPLACE_WITH_GIT_REPO_LINK
   ```

   - Replace `TODO: REPLACE_WITH_GIT_REPO_LINK` with the actual Git repository URL.

3. **Navigate to the project directory**:

   ```bash
   cd FIT-API
   ```

4. **Check for updates**:

   To pull the latest changes from the repository, use:

   ```bash
   git pull origin main
   ```

   Replace `main` with the branch you are working on, if different.

#### Option 2: Using a Web Browser

1. **Open your web browser** and go to the Git repository page: `TODO: REPLACE_WITH_GIT_REPO_LINK`.
2. **Download the repository as a ZIP file**:
   - Look for a button or option that says **"Code"** or **"Download"**.
   - Click on **"Download ZIP"** to download the repository files to your local machine.
3. **Extract the ZIP file**:
   - Use your file explorer to navigate to the downloaded ZIP file and extract it to a directory of your choice.
   - Rename the extracted folder to `FIT-API` if necessary.

4. **Open the project folder**:
   - Use your file explorer to navigate to the directory where you extracted the repository files (e.g., `FIT-API`).


### Database creation
The API requires a database. In previous versions of this repository, the database was supplied, which is no longer the case. To create the database, please follow these steps:
1. Head to the sister repository [FIT_scripts_public](https://github.com/corsus-GmbH/FIT_scripts_public) and follow instructions there to create the CSV files needed for the database
2. Copy the created files into `database_creation/input/`
3. Run the script `database_creation/create_full_database.py`
4. Copy the created file from `database_creation/output/` and save under `data/FIT.db` 


### Basic Docker Setup

Once you have the repository, ensure you are in the project directory (`FIT-API`) before running any Docker commands.

1. **Build the Docker image**:

   ```bash
   docker build -t fit-api:latest .
   ```

   - **`fit-api`**: This is the image name. You can change it to a name that makes sense for your project.
   - **`latest`**: This is the tag. You can change it to a version number like `v1.0.0` if you prefer to version your images.

2. **Run the Docker container**:

   ```bash
   docker run -d --name fit-api-container -p 8080:80 fit-api:latest
   ```

   - **`--name fit-api-container`**: This assigns a custom name to the container. Feel free to change it to something meaningful for your use case.
   - **`8080:80`**: This maps port 80 inside the container to port 8080 on your machine. You can change the first number (`8080`) to another port if 8080 is already in use.
   - **`fit-api:latest`**: This refers to the image name and tag you built earlier. Use the name and tag that you set during the `docker build` command.

3. **Verify that the container is running**:

   ```bash
   docker ps
   ```

   The container should appear in the list with the name you assigned (`fit-api-container`).

4. **Stop the container** when needed:

   ```bash
   docker stop fit-api-container
   ```

   Replace `fit-api-container` with the name of your container if you used a different one.

### Advanced Docker Setup: Managing Logs

To ensure log files are accessible and persistent, you can bind the logs directory to a location outside the container. This is useful for monitoring and debugging without needing to access the container directly.

#### Binding Log Files to External Storage

1. **Run the container with log file binding**:

   ```bash
   docker run -d --name fit-api-container -p 8080:80 -v /path/to/local/logs:/usr/src/FIT/logs fit-api:latest
   ```

   - **`/path/to/local/logs`**: Replace this with the path to the directory on your local machine where you want to save the logs.
   - **`fit-api-container`**, **`8080:80`**, and **`fit-api:latest`**: These parameters are customizable as described in the basic setup.

2. **Viewing and Managing Logs**:
   - The logs are saved in the directory you specified during container setup.
   - These are simple text files (`.log`) that can be accessed and read using any standard text editor or log management tool.
   - Common log files include:
     - **`app.log`**: General application-level events, warnings, errors, and debug information.
     - **`access.log`**: HTTP request logs, including request methods, paths, and response statuses.
     - **`sql.log`**: Logs related to database interactions and SQL queries.

   Navigate to the directory on your host system where the logs are stored and use any tool you prefer to view and manage the logs.

#### Using Docker Volumes for Logs (Alternative)

Alternatively, you can use Docker volumes to manage logs:

1. **Create a Docker volume**:

   ```bash
   docker volume create fit-api-logs
   ```

   - **`fit-api-logs`**: This is the name of the volume. You can choose any name that makes sense for your project.

2. **Run the container with the volume**:

   ```bash
   docker run -d --name fit-api-container -p 8080:80 -v fit-api-logs:/usr/src/FIT/logs fit-api:latest
   ```

   - **`fit-api-logs`**: The name of the Docker volume you created.
   - **`fit-api-container`**, **`8080:80`**, and **`fit-api:latest`**: These parameters are customizable as described in the basic setup.

### Updating the Docker Image

To update the Docker image with new code changes:

1. **Rebuild the image** with a new version tag:

   ```bash
   docker build -t fit-api:v1.1.1 .
   ```

   - **`fit-api:v1.1.1`**: Update the image name and tag to reflect the new version.

2. **Stop and remove the old container**:

   ```bash
   docker stop fit-api-container
   docker rm fit-api-container
   ```

   Replace `fit-api-container` with the name of your container if you used a different one.

3. **Run a new container** with the updated image:

   ```bash
   docker run -d --name fit-api-container -p 8080:80 -v /path/to/local/logs:/usr/src/FIT/logs fit-api:v1.1.1
   ```

   - **`fit-api:v1.1.1`**: Use the updated image name and tag.
   - **`/path/to/local/logs`**: Ensure this path is correct for your setup if you are binding logs externally.

### Additional Tips

- **Container Shell Access**: Note that the `FIT-API` container is based on an Alpine Linux image, so you will use `sh` instead of `bash` for shell access:

  ```bash
  docker exec -it fit-api-container /bin/sh
  ```

  For more details on Alpine's shell environment, see the [Alpine Linux Documentation](https://wiki.alpinelinux.org/wiki/Alpine_Linux:FAQ).

- **Cleaning Up**: Remove unused Docker images to free up space:

  ```bash
  docker image prune
  ```

By following these instructions, you can set up a Docker environment for `FIT-API` that supports persistent logging, allowing for easier monitoring and debugging.


## Using the API

The `FIT-API` is designed to interact with Life Cycle Inventory (LCI) data, allowing you to calculate the environmental impact of various recipes. This guide will walk you through a typical usage scenario, from discovering available items to calculating the environmental impact using the main `calculate-recipe` endpoint.

### Step 1: Accessing the API Documentation

To get familiar with the API, you’ll first access its interactive documentation. The API provides two types of automatically generated documentation: **Swagger UI** and **ReDoc**.

#### Swagger UI (Main Documentation)

1. **Swagger UI**: Open your web browser and go to:

   ```
   http://localhost:<YOUR_PORT>/docs
   ```

   Replace `<YOUR_PORT>` with the port you specified when starting the Docker container. For example, if you ran the container with `-p 8080:80`, use:

   ```
   http://localhost:8080/docs
   ```

   In Swagger UI, you can interact with the API directly by filling out forms, executing requests, and viewing live responses. This is the primary interface for testing the API and getting a hands-on experience with how the endpoints work.

#### Alternative Documentation: ReDoc

ReDoc is another type of documentation provided by FastAPI, offering a more structured, read-only view of the API's endpoints. While you can’t interact with the API directly in ReDoc, it provides a comprehensive overview of each endpoint’s parameters, expected responses, and descriptions.

1. **Access ReDoc**: Use the following URL in your browser:

   ```
   http://localhost:<YOUR_PORT>/redoc
   ```

   For example:

   ```
   http://localhost:8080/redoc
   ```

2. **Explore the API**:
   - ReDoc offers a clean and organized view of the API, making it easy to understand the available endpoints and their requirements.
   - This documentation is particularly useful for getting an overview of the API’s capabilities before interacting with it in Swagger UI.

### Step 2: Exploring Available Items

Before calculating environmental impacts, you’ll need to know which LCI items are available for analysis.

1. **Find the `/items/` endpoint** in Swagger UI:
   - Scroll through the list of endpoints or use the search function to find the **`GET /items/`** endpoint.

2. **Execute the Request**:
   - Click **"Try it out"** and then **"Execute"**. This will show you a list of available items in the database, each with a unique identifier.

3. **Review the Items**:
   - Note the item identifiers, formatted as `item_id-country_acronym` (e.g., `20134-FRA`). You’ll use these identifiers in the next steps.

### Step 3: Calculating Environmental Impact

Once you have the item identifiers, you can calculate the environmental impact of a recipe using the `calculate-recipe` endpoint.

1. **Find the `/calculate-recipe/` endpoint** in Swagger UI.

2. **Open the Endpoint Form**:
   - Click on the endpoint to expand it, then click **"Try it out"**.

3. **Provide Input Data**:
   - Enter the items and weighting scheme details in the provided fields. For example:

     ```json
     {
       "items": {
         "20134-FRA": 1.2,
         "24070-FRA": 0.5
       },
       "weighting_scheme_name": "ef31_r0510"
     }
     ```

4. **Execute the Request**:
   - Click **"Execute"** to send the request. The API will calculate the environmental impact based on your input.

5. **Review the Results**:
   - The response will be displayed directly in Swagger UI, showing the environmental impact of the specified items and the overall recipe.

### Step 4: Experimenting with Recipes

Now that you've seen how to retrieve and calculate data, you can experiment:

1. **Modify Item Quantities**: Change the amounts in the `items` field to see how it impacts the environmental scores.
2. **Test Different Weighting Schemes**: Use another `weighting_scheme_name` or `weighting_scheme_id` to compare results.
3. **Re-run the Request**: Adjust the inputs and click **"Execute"** to see the updated calculations.

### Understanding the Schemas

In the API documentation (both in Swagger UI and ReDoc), you'll encounter several **schemas**. These schemas define the structure of the data expected by the API endpoints or returned as responses. The schemas are visible because they are necessary for interacting with the key endpoints, and they provide clear guidelines on the format and content of the data you need to supply.

#### What Are Schemas?

Schemas are data models that describe the shape and requirements of the input and output data for each endpoint:

- **Input Schemas**: Define the format for the data you need to provide when making a request to an endpoint. They specify required fields, data types, and expected formats.
- **Output Schemas**: Describe the format of the data you will receive in response to a request. This helps you understand how to interpret the results and where to find the relevant information.

#### Why Are Only Certain Schemas Visible?

To keep the documentation clear and focused, only the schemas that are directly relevant to the endpoints are visible. This means that you’ll only see the schemas you need to interact with the API endpoints effectively. These include:

1. **InputData Schema**:
   - Used to structure the data you provide when making a `POST` request to the `calculate-recipe` endpoint.
   - Specifies how to format the items and weighting scheme for environmental impact calculations.

2. **OutputData Schema**:
   - Defines the structure of the data returned by the `calculate-recipe` endpoint.
   - Provides a detailed breakdown of the environmental impact calculations, including scores and grades for each item and the overall recipe.

3. **ItemInfo Schema**:
   - Appears when you retrieve item details from the `items` endpoint.
   - Helps you understand the information associated with each item, such as product name, category, and whether proxy data is used.

Each schema includes descriptions and example data in the API documentation to help you understand the data requirements and response formats. Refer to these schemas whenever you need clarification on how to format your request data or interpret the responses from the API.

### Tips for a Smooth Experience

- **Use Swagger UI** for all testing and interaction with the API. It’s the best way to visualize how different inputs affect the results.
- **Bookmark the API Documentation URLs**: Save the URLs for Swagger UI and ReDoc in your web browser’s bookmarks. This way, you can quickly access the API documentation anytime you need to refer to endpoint details or modify your requests.
- **Explore with ReDoc**: Use ReDoc to get a structured overview of the API endpoints and see detailed parameter descriptions.

### Troubleshooting Common Issues

- **Missing Items**: Ensure you’ve entered correct item identifiers from the `/items/` endpoint.
- **Weighting Scheme**: Verify that you’re specifying the weighting scheme using either `weighting_scheme_name` or `weighting_scheme_id`. Only one should be provided.
- **Connection Issues**: Make sure the Docker container is running and accessible through the correct port.




## Logging Setup

The application uses a structured logging system to capture and manage logs efficiently, primarily utilizing the `uvicorn` and `sqlalchemy` loggers. The logging configuration is set up to capture different aspects of the application's behavior, including database operations, API requests, and application-level events.

### Log Directory Structure

In the Docker container, all log files are stored in the `logs/` directory located at the root of the application. Here's a description of the folder and file structure:

```
/usr/src/FIT
└── logs/
    ├── app.log
    ├── access.log
    ├── sql.log
    ├── tracebacks/
    │   └── [error_traceback_files]
    └── docker/
        ├── apk_update.log
        ├── openssl_upgrade.log
        └── pip_install.log
```

- **`logs/`**: The main directory where all log files are stored.
- **`app.log`**: Captures general application-level events, warnings, errors, and debug information if `LOG_LEVEL` is set to a detailed level.
- **`access.log`**: Logs access requests to the API, including request methods, paths, and response statuses.
- **`sql.log`**: Records database interactions and SQL queries. Initially set to log only essential information during the database creation phase, the log level is adjusted dynamically post-startup to reflect the desired verbosity.
- **`tracebacks/`**: A subdirectory to store detailed error tracebacks for debugging purposes. The number of stored traceback files can be configured in `debug.env`.
- **`docker/`**: Contains logs specifically related to the Docker build process.
  - **`apk_update.log`**: Captures the output of the `apk update` command during the Docker build. This helps trace issues related to package updates in the Alpine Linux environment.
  - **`openssl_upgrade.log`**: Logs the installation of specific packages, like `openssl`. Any issues with package versions or conflicts are recorded here.
  - **`pip_install.log`**: Captures the output of the `pip install` process, providing insight into potential package installation errors or dependency conflicts.

### How Logging Works

The logging configuration is managed via a central module (`logging_setup.py`) which handles initialization and log level adjustments:

1. **Setup Phase**: During the application's startup, the loggers are initialized with different settings to ensure smooth startup and debugging capabilities.
   - The **SQLAlchemy** logger (`sql.log`) is initially set to log at the `INFO` level during the database creation phase to avoid excessive logging. Once the database setup is complete, the logging level is adjusted to the value specified in `debug.env`.
   - The **Uvicorn** logger starts with a minimum log level of `INFO` during the startup sequence to capture essential startup information. After the application has fully initialized, it adjusts to the desired log level specified in `LOG_LEVEL` to provide the appropriate level of detail.

2. **Log Files**:
   - **`app.log`**: Handles general logging for the application, including API events, configuration details, and errors.
   - **`access.log`**: Captures HTTP requests, including request methods, paths, and response statuses.
   - **`sql.log`**: Dedicated to database interactions, capturing SQL query logs and database-related errors.

3. **Delayed Log Level Adjustment**: The `uvicorn` and `SQLAlchemy` loggers initially operate with conservative log levels (`INFO`) during the setup to reduce noise, particularly during database creation. After the startup sequence completes, the log levels are dynamically adjusted using a delayed task to match the `LOG_LEVEL` specified in `debug.env`.

### Docker Logging Setup

In addition to application-level logging, the Docker build process captures several steps to aid in debugging any issues during the image creation. These logs are stored separately in the `logs/docker` directory within the Docker image.

#### Key Docker Commands:

1. **`apk update`**: Updates the Alpine Linux package index. Output is logged to `apk_update.log`.
2. **`apk add`**: Installs required packages, such as `openssl`. The command output is logged to `openssl_upgrade.log`.
3. **`pip install`**: Installs Python dependencies listed in `requirements.txt`. The output is logged to `pip_install.log`.

### How to Access Logs

If the container is running or you have access to the Docker image, you can check the logs using the following commands:

```bash
# Enter the running container
docker exec -it <container_id> /bin/sh

# Navigate to the logs directory
cd /usr/src/FIT/logs

# View application logs
cat app.log
cat access.log
cat sql.log

# View Docker-related logs
cd docker
cat apk_update.log
cat openssl_upgrade.log
cat pip_install.log

# View error tracebacks (if any exist)
cd ../tracebacks
cat traceback_[timestamp].log
```

### Configuration via `debug.env`

The `debug.env` file is used to control various aspects of the logging behavior:

- **`SHOW_TRACEBACK_IN_ENDPOINT`**: When set to `true`, enables tracebacks to be displayed in HTTP responses if an error occurs. **This is a security risk and should only be used for debugging purposes.** In production, ensure this is set to `false` to prevent exposing internal application details.
- **`LOG_LEVEL`**: Specifies the desired logging level. Possible values include `DEBUG`, `INFO`, `WARNING`, `ERROR`, etc. This setting controls the verbosity of the logs captured in `app.log`, `access.log`, and `sql.log`.
- **`MAX_TRACEBACK_FILES`**: Defines the maximum number of traceback files stored in the `tracebacks/` directory. This helps manage disk space when dealing with a large number of errors.
- **`SHOW_ACCESS_LOGS`**: Controls whether access logs are displayed in the console. When set to `false`, access logs are only stored in `access.log` and not printed to the console.

### Tips for Debugging

- Ensure that `SHOW_TRACEBACK_IN_ENDPOINT` is set to `true` only when you need to debug errors with detailed tracebacks in HTTP responses.
- Adjust the `LOG_LEVEL` to `DEBUG` or `INFO` depending on the amount of detail you need.
- If your application generates too many tracebacks, consider lowering the verbosity or increasing the `MAX_TRACEBACK_FILES` limit.
- The `SHOW_ACCESS_LOGS` flag controls whether access logs should be visible in the console output. Disable this in production for cleaner logs.
- If the Docker image build fails, you can inspect the logs in the `logs/docker/` directory to identify where the problem occurred.

By organizing Docker-specific logs separately, the application maintains a clear boundary between runtime logs and build logs, facilitating smoother debugging processes for both developers and operators.


### Licence
This work is licensed under the Creative Commons Attribution 4.0 International License. Please refer to LICENCE file.