from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class CheckoutRequest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=120)
    cedula: str = Field(..., min_length=4, max_length=20)
    phone: str = Field(..., min_length=7, max_length=20)
    email: EmailStr
    city: str = Field("Colombia", min_length=2, max_length=80)
    tickets: List[str] = Field(..., min_items=5)
    payment_method: str = Field("nequi")
    notes: Optional[str] = None

class RandomTicketsRequest(BaseModel):
    count: int = Field(5, ge=5, le=500)

class CheckWinnerRequest(BaseModel):
    number: str = Field(..., min_length=1, max_length=4)

class AdminLoginRequest(BaseModel):
    pin: str

class ManualSaleRequest(BaseModel):
    full_name: str
    cedula: str
    phone: str
    email: str
    city: str = "Colombia"
    tickets: List[str]
    payment_method: str = "efectivo"
    notes: Optional[str] = None
