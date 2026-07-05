.PHONY: ci-local
# One-command pre-push gate — the same steps CI runs, hard-failing on first red.
ci-local:
	uv sync --extra dev
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy sm_resolver
	uv run pytest -v
	uv run python examples/corroborate_sources.py
	uv run python examples/custom_layer.py
