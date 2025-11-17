"""Entrypoint for running the FastAPI application with uvicorn."""
from __future__ import annotations

import uvicorn


def main() -> None:
    """Launch the FastAPI server."""

    uvicorn.run("cg_rera_extractor.api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
