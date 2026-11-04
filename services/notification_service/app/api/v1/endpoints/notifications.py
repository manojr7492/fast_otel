import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, status
from app.core.config import settings
from app.core.telemetry import get_tracer
from app.schemas.notification import NotificationResponse, NotificationSendRequest

logger = logging.getLogger(settings.SERVICE_NAME)
tracer = get_tracer("notifications_endpoint")

router = APIRouter()

# In-memory audit trail of dispatched notifications
_notifications_audit: List[NotificationResponse] = []


@router.post(
    "/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispatch Notification Event",
)
async def send_notification(payload: NotificationSendRequest) -> NotificationResponse:
    with tracer.start_as_current_span("notification.process") as span:
        notification_id = str(uuid.uuid4())
        span.set_attribute("notification.id", notification_id)
        span.set_attribute("notification.recipient_email", payload.recipient_email)
        span.set_attribute("notification.event_type", payload.event_type)
        span.set_attribute("notification.priority", payload.priority or "NORMAL")

        with tracer.start_as_current_span("notification.render_template") as render_span:
            render_span.set_attribute("template.type", payload.event_type)
            rendered_subject = f"[{settings.PROJECT_NAME}] Update regarding {payload.event_type}"

        with tracer.start_as_current_span("notification.dispatch_channel") as channel_span:
            channel_span.set_attribute("channel.provider", "mock_smtp_provider")
            channel_span.set_attribute("channel.status", "DELIVERED")

        response = NotificationResponse(
            notification_id=notification_id,
            recipient_email=payload.recipient_email,
            event_type=payload.event_type,
            status="DELIVERED",
            dispatched_at=datetime.now(timezone.utc),
            details=f"Notification delivered for {payload.recipient_name} ({rendered_subject})",
        )

        _notifications_audit.append(response)
        if len(_notifications_audit) > 100:
            _notifications_audit.pop(0)

        logger.info(
            "Successfully processed notification %s for %s [event: %s]",
            notification_id,
            payload.recipient_email,
            payload.event_type,
        )

        return response


@router.get(
    "/history",
    response_model=List[NotificationResponse],
    summary="List Recent Notification Events",
)
async def list_notifications() -> List[NotificationResponse]:
    with tracer.start_as_current_span("notification.list_history") as span:
        span.set_attribute("audit.count", len(_notifications_audit))
        return list(reversed(_notifications_audit))

