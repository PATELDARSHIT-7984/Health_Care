from  pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from api.models import Bill, Appointment, Prescription

class BillSchema(BaseModel):
    prescription : int
    quantity : int = Field(gt=0)
    instance_id : Optional[int] = None

    @model_validator(mode="after")
    def validate_bill(self):
        if not Prescription.objects.filter(id = self.prescription).exists():
            raise ValueError("Prescription does not exist")
        
        qs = Bill.objects.filter(prescription_id = self.prescription)

        if self.instance_id:
            qs = qs.exclude(id = self.instance_id)
        
        if qs.exists():
            raise ValueError("Bill already exists for this prescription")
        
        return self
