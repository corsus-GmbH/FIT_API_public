#!/bin/sh

# Setup the working directory (assumes the script is run within the Docker container at /usr/src/FIT)
cd /usr/src/FIT || exit

# Create a virtual environment named 'venv' in the current directory
python -m venv venv --system-site-packages

# Activate the virtual environment
. venv/bin/activate

# Install main and test dependencies
pip install --no-cache-dir -r tests/test_requirements.txt

# Run the tests
python -m pytest ./tests

# After running tests, ask the user if they want to run more tests
echo "Do you want to run more tests? (yes/no)"
read answer

if [ "$answer" != "yes" ]; then
    # Deactivate and remove the virtual environment if no more tests are required
    deactivate
    rm -rf venv
    echo "Virtual environment removed and cleaned up."
    exit 0
else
    echo "You can continue to use the environment. Run 'deactivate' to exit and 'rm -rf venv' to clean up manually when done."
fi

# If user opts to run more tests, the script ends without tearing down the environment.
# User must manually deactivate and remove the virtual environment later.
