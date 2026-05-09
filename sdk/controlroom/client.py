"""HTTP client for sending eval results to the Control Room backend."""

import logging
import os

import requests

from controlroom.models import EvalResult

logger = logging.getLogger(__name__)

BACKEND_URL: str = os.environ.get("CONTROLROOM_BACKEND_URL", "http://127.0.0.1:8000")


def send_results(eval_result: EvalResult) -> str | None:
    """Send an eval result to the backend and return the assigned run id.

    POSTs the serialized ``eval_result`` to ``{BACKEND_URL}/runs``. On a 200
    response, returns the ``run_id`` from the JSON body. On any failure
    (connection error, timeout, non-200 status, malformed response), logs a
    warning and returns ``None`` so the calling eval run can still complete.
    """
    url = f"{BACKEND_URL}/runs"
    try:
        response = requests.post(url, json=eval_result.model_dump())
        if response.status_code != 200:
            logger.warning(
                "Failed to send eval results to %s: status %s, body %s",
                url,
                response.status_code,
                response.text,
            )
            return None
        run_id: str = response.json()["run_id"]
        return run_id
    except Exception as error:
        logger.warning("Failed to send eval results to %s: %s", url, error)
        return None
