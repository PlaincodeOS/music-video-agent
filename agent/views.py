from __future__ import annotations

import json
import logging

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from agent.services import build_request_from_payload, run_generation


LOGGER = logging.getLogger(__name__)


def index(request: HttpRequest):
    return render(request, "agent/index.html")


@csrf_exempt
def generate_video(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    try:
        run_request = build_request_from_payload(payload)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    try:
        result = run_generation(run_request)
    except Exception as exc:
        LOGGER.exception("Video generation failed")
        return JsonResponse({"error": str(exc)}, status=500)

    return JsonResponse(
        {
            "status": "ok",
            "file_id": result.file_id,
            "name": result.name,
            "web_view_link": result.web_view_link,
            "web_content_link": result.web_content_link,
        }
    )
