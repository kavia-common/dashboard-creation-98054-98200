.PHONY: install lint format run openapi

install:
\tpip install -r requirements.txt

lint:
\tflake8

format:
\tpython -m pip install black==24.10.0 || true
\tblack src

run:
\tuvicorn src.api.main:app --host 0.0.0.0 --port 3001 --proxy-headers

openapi:
\tpython -m src.api.generate_openapi
