from collections.abc import Generator
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas import (
    AttendanceCreate,
    AttendanceResponse,
    DashboardResponse,
    PaymentResponse,
    PaymentStatus,
    StudentDetailResponse,
    StudentResponse,
)
from app.services import (
    create_attendance,
    get_dashboard_summary,
    get_student_detail,
    list_attendance,
    list_payments,
    list_students,
    list_students_by_class,
    mark_payment_paid,
)


app = FastAPI(
    title="Academy Student Manager API",
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


@app.get("/", include_in_schema=False)
def read_index() -> FileResponse:
    return FileResponse("app/static/index.html")


def get_db() -> Generator[Session, None, None]:
    session: Session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@app.get(
    "/api/dashboard",
    response_model=DashboardResponse,
)
def read_dashboard(
    session: Session = Depends(get_db),
) -> dict[str, int]:
    return get_dashboard_summary(session)


@app.get(
    "/api/students",
    response_model=list[StudentResponse],
)
def read_students(
    grade: int | None = Query(default=None, ge=1, le=3),
    class_id: int | None = Query(default=None, ge=1),
    session: Session = Depends(get_db),
):
    return list_students(
        session=session,
        grade=grade,
        class_id=class_id,
    )


@app.get(
    "/api/students/{student_id}",
    response_model=StudentDetailResponse,
)
def read_student(
    student_id: int,
    session: Session = Depends(get_db),
):
    try:
        return get_student_detail(
            session=session,
            student_id=student_id,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@app.get(
    "/api/classes/{class_id}/students",
    response_model=list[StudentResponse],
)
def read_students_by_class(
    class_id: int,
    session: Session = Depends(get_db),
):
    return list_students_by_class(
        session=session,
        class_id=class_id,
    )


@app.get(
    "/api/attendance",
    response_model=list[AttendanceResponse],
)
def read_attendance(
    attendance_date: date | None = Query(
        default=None,
        alias="date",
    ),
    class_id: int | None = Query(default=None, ge=1),
    student_id: int | None = Query(default=None, ge=1),
    session: Session = Depends(get_db),
):
    return list_attendance(
        session=session,
        attendance_date=attendance_date,
        class_id=class_id,
        student_id=student_id,
    )


@app.post(
    "/api/attendance",
    response_model=AttendanceResponse,
    status_code=201,
)
def add_attendance(
    data: AttendanceCreate,
    session: Session = Depends(get_db),
):
    try:
        return create_attendance(
            session=session,
            data=data,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@app.get(
    "/api/payments",
    response_model=list[PaymentResponse],
)
def read_payments(
    month: str | None = None,
    status: PaymentStatus | None = None,
    class_id: int | None = Query(default=None, ge=1),
    session: Session = Depends(get_db),
):
    return list_payments(
        session=session,
        billing_month=month,
        status=status,
        class_id=class_id,
    )


@app.patch(
    "/api/payments/{payment_id}",
    response_model=PaymentResponse,
)
def pay_payment(
    payment_id: int,
    session: Session = Depends(get_db),
):
    try:
        return mark_payment_paid(
            session=session,
            payment_id=payment_id,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error