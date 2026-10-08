from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AttendanceStatus = Literal["출석", "지각", "결석"]
PaymentStatus = Literal["납부", "미납"]


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    grade: int
    school: str
    guardian_phone: str
    status: str
    class_id: int


class AttendanceCreate(BaseModel):
    student_id: int = Field(gt=0)
    attendance_date: date
    status: AttendanceStatus
    note: str | None = Field(default=None, max_length=255)


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attendance_id: int
    student_id: int
    attendance_date: date
    status: AttendanceStatus
    note: str | None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    student_id: int
    billing_month: str
    amount: int = Field(gt=0)
    status: PaymentStatus
    paid_at: date | None


class StudentDetailResponse(BaseModel):
    student: StudentResponse
    recent_attendance: list[AttendanceResponse]
    current_payment: PaymentResponse | None


class DashboardResponse(BaseModel):
    total_students: int
    grade_1_students: int
    grade_2_students: int
    grade_3_students: int

    today_present: int
    today_late: int
    today_absent: int

    monthly_paid: int
    monthly_unpaid: int