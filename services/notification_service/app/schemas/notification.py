from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, Field


class NotificationSendRequest(BaseModel):
    recipient_email: EmailStr
    recipient_name: Optional[str] = "Customer"
    event_type: str = Field(..., description="E.g. WELCOME_USER, PASSWORD_RESET, ORDER_CONFIRMATION")
    data: Dict[str, Any] = Field(default_factory=dict, description="Metadata and templating context")
    priority: Optional[str] = Field(default="NORMAL", description="LOW, NORMAL, HIGH, CRITICAL")


class NotificationResponse(BaseModel):
    notification_id: str
    recipient_email: str
    event_type: str
    status: str
    dispatched_at: datetime
    details: Optional[str] = None

