
set -eo pipefail

COLOR_GREEN=`tput setaf 2;`
COLOR_NC=`tput sgr0;`  # No Color

echo "Starting isort"
poetry run isort .
echo "OK"

echo "Starting black"
poetry run black .
echo "OK"


#echo "Starting ruff"
#poetry run ruff check --select I --fix
#poetry run ruff check --fix
#echo "OK"

echo "Starting mypy"
#poetry run dmypy stop
poetry run dmypy run -- .
#poetry run mypy .
echo "OK"

echo "Starting pytest with coverage"
poetry run coverage run -m pytest
poetry run coverage report -m
poetry run coverage html
echo "OK"

#echo "Starting pytest with coverage"
#poetry run pytest --cov=. --cov-report=term-missing --cov-report=html
#echo "OK"

echo "${COLOR_GREEN}ALL tests passed successfully!${COLOR_NC}"
