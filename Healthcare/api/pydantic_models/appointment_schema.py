from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from django.utils import timezone

from api.models import Appointment


class AppointmentSchema(BaseModel):
    doctor: int
    date: datetime
    user: int | None = None   # optional (we can pass later if needed)

    # ✅ FIELD LEVEL VALIDATION
    @field_validator("date")
    @classmethod
    def validate_future_date(cls, value):
        if value <= timezone.now():
            raise ValueError("Appointment date must be in the future")
        return value

    # ✅ MODEL LEVEL VALIDATION
    @model_validator(mode="after")
    def validate_duplicate_appointment(self):
        if self.user:
            exists = Appointment.objects.filter(
                user_id=self.user,
                doctor_id=self.doctor,
                date=self.date
            ).exists()

            if exists:
                raise ValueError("You already have an appointment at this time")

        return self

