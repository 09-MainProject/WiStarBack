
set -eo pipefail

COLOR_GREEN=`tput setaf 2;`
COLOR_NC=`tput sgr0;`  # No Color

echo "Starting black"
poetry run black .
echo "OK"

echo "Starting isort"
poetry run isort .
echo "OK"

echo "Starting mypy"
poetry run dmypy run -- .
echo "OK"

echo "Starting pytest with coverage"
poetry run pytest --cov=패키지명 --cov-report=term-missing --cov-report=html
echo "OK"


echo "${COLOR_GREEN}ALL tests passed successfully!${COLOR_NC}"
