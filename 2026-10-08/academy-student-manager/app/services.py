from datetime import date

from sqlalchemy.orm import Session

from app import repositories
from app.models import Attendance, Payment, Student
from app.schemas import AttendanceCreate


def list_students(
    session: Session,
    grade: int | None = None,
    class_id: int | None = None,
) -> list[Student]:
    return repositories.get_students(
        session=session,
        grade=grade,
        class_id=class_id,
    )


def get_student_detail(
    session: Session,
    student_id: int,
) -> dict[str, object]:
    student: Student | None = repositories.get_student(
        session,
        student_id,
    )

    if student is None:
        raise LookupError("학생을 찾을 수 없습니다.")

    attendance: list[Attendance] = repositories.get_attendance(
        session=session,
        student_id=student_id,
    )

    current_month: str = date.today().strftime("%Y-%m")

    payments: list[Payment] = repositories.get_payments(
        session=session,
        billing_month=current_month,
    )

    current_payment: Payment | None = next(
        (
            payment
            for payment in payments
            if payment.student_id == student_id
        ),
        None,
    )

    return {
        "student": student,
        "recent_attendance": attendance[:3],
        "current_payment": current_payment,
    }


def list_students_by_class(
    session: Session,
    class_id: int,
) -> list[Student]:
    return repositories.get_students_by_class(
        session,
        class_id,
    )


def list_attendance(
    session: Session,
    attendance_date: date | None = None,
    class_id: int | None = None,
    student_id: int | None = None,
) -> list[Attendance]:
    return repositories.get_attendance(
        session=session,
        attendance_date=attendance_date,
        class_id=class_id,
        student_id=student_id,
    )


def create_attendance(
    session: Session,
    data: AttendanceCreate,
) -> Attendance:
    student: Student | None = repositories.get_student(
        session,
        data.student_id,
    )

    if student is None:
        raise LookupError("학생을 찾을 수 없습니다.")

    existing: Attendance | None = (
        repositories.get_attendance_by_student_date(
            session=session,
            student_id=data.student_id,
            attendance_date=data.attendance_date,
        )
    )

    if existing is not None:
        raise ValueError("해당 학생의 출결이 이미 등록되어 있습니다.")

    attendance = Attendance(
        student_id=data.student_id,
        attendance_date=data.attendance_date,
        status=data.status,
        note=data.note,
    )

    return repositories.add_attendance(
        session,
        attendance,
    )


def list_payments(
    session: Session,
    billing_month: str | None = None,
    status: str | None = None,
    class_id: int | None = None,
) -> list[Payment]:
    return repositories.get_payments(
        session=session,
        billing_month=billing_month,
        status=status,
        class_id=class_id,
    )


def mark_payment_paid(
    session: Session,
    payment_id: int,
) -> Payment:
    payment: Payment | None = repositories.get_payment(
        session,
        payment_id,
    )

    if payment is None:
        raise LookupError("수납 정보를 찾을 수 없습니다.")

    if payment.status == "납부":
        raise ValueError("이미 납부 처리된 항목입니다.")

    payment.status = "납부"
    payment.paid_at = date.today()

    return repositories.save_payment(
        session,
        payment,
    )


def get_dashboard_summary(
    session: Session,
) -> dict[str, int]:
    students: list[Student] = repositories.get_students(session)

    today: date = date.today()

    attendance: list[Attendance] = repositories.get_attendance(
        session=session,
        attendance_date=today,
    )

    current_month: str = today.strftime("%Y-%m")

    payments: list[Payment] = repositories.get_payments(
        session=session,
        billing_month=current_month,
    )

    return {
        "total_students": len(students),
        "grade_1_students": sum(
            student.grade == 1 for student in students
        ),
        "grade_2_students": sum(
            student.grade == 2 for student in students
        ),
        "grade_3_students": sum(
            student.grade == 3 for student in students
        ),
        "today_present": sum(
            record.status == "출석" for record in attendance
        ),
        "today_late": sum(
            record.status == "지각" for record in attendance
        ),
        "today_absent": sum(
            record.status == "결석" for record in attendance
        ),
        "monthly_paid": sum(
            payment.status == "납부" for payment in payments
        ),
        "monthly_unpaid": sum(
            payment.status == "미납" for payment in payments
        ),
    }