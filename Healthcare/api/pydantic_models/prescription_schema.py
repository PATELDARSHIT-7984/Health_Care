from typing import Optional

from pydantic import BaseModel, field_validator, model_validator
from api.models import Appointment, Prescription, Medicine

class PrescriptionSchema(BaseModel):
    appointment : int
    medication : int
    dosage : str
    instance_id : Optional[int] = None

    @field_validator("dosage")
    @classmethod
    def validate_dosage(cls,value):
        if not value or value.strip()== "":
            raise ValueError("Dosage cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_prescription(self):
        if not Medicine.objects.filter(id = self.medication).exists():
            raise ValueError("Medication does not exist")
        
        if not Appointment.objects.filter(id = self.appointment).exists():
            raise ValueError("No appointment found for this ID", self.appointment)
        
        qs = Prescription.objects.filter(appointment_id = self.appointment)

        if self.instance_id:
            qs = qs.exclude(id = self.instance_id)
        
        if qs.exists():
            raise ValueError("Prescription already exists for this appointment")
        
        return self
    