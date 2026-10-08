from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Attendance, Payment, Student


def get_students(
    session: Session,
    grade: int | None = None,
    class_id: int | None = None,
) -> list[Student]:
    stmt: Select[tuple[Student]] = select(Student)

    if grade is not None:
        stmt = stmt.where(Student.grade == grade)

    if class_id is not None:
        stmt = stmt.where(Student.class_id == class_id)

    stmt = stmt.order_by(Student.student_id)

    return list(session.scalars(stmt).all())


def get_student(
    session: Session,
    student_id: int,
) -> Student | None:
    return session.get(Student, student_id)


def get_students_by_class(
    session: Session,
    class_id: int,
) -> list[Student]:
    stmt: Select[tuple[Student]] = (
        select(Student)
        .where(Student.class_id == class_id)
        .order_by(Student.student_id)
    )

    return list(session.scalars(stmt).all())


def get_attendance(
    session: Session,
    attendance_date: date | None = None,
    class_id: int | None = None,
    student_id: int | None = None,
) -> list[Attendance]:
    stmt: Select[tuple[Attendance]] = select(Attendance)

    if class_id is not None:
        stmt = stmt.join(
            Student,
            Attendance.student_id == Student.student_id,
        ).where(Student.class_id == class_id)

    if attendance_date is not None:
        stmt = stmt.where(
            Attendance.attendance_date == attendance_date
        )

    if student_id is not None:
        stmt = stmt.where(
            Attendance.student_id == student_id
        )

    stmt = stmt.order_by(
        Attendance.attendance_date.desc(),
        Attendance.student_id,
    )

    return list(session.scalars(stmt).all())


def get_attendance_by_student_date(
    session: Session,
    student_id: int,
    attendance_date: date,
) -> Attendance | None:
    stmt: Select[tuple[Attendance]] = select(Attendance).where(
        Attendance.student_id == student_id,
        Attendance.attendance_date == attendance_date,
    )

    return session.scalar(stmt)


def add_attendance(
    session: Session,
    attendance: Attendance,
) -> Attendance:
    session.add(attendance)
    session.commit()
    session.refresh(attendance)

    return attendance


def get_payments(
    session: Session,
    billing_month: str | None = None,
    status: str | None = None,
    class_id: int | None = None,
) -> list[Payment]:
    stmt: Select[tuple[Payment]] = select(Payment)

    if class_id is not None:
        stmt = stmt.join(
            Student,
            Payment.student_id == Student.student_id,
        ).where(Student.class_id == class_id)

    if billing_month is not None:
        stmt = stmt.where(
            Payment.billing_month == billing_month
        )

    if status is not None:
        stmt = stmt.where(
            Payment.status == status
        )

    stmt = stmt.order_by(Payment.student_id)

    return list(session.scalars(stmt).all())


def get_payment(
    session: Session,
    payment_id: int,
) -> Payment | None:
    return session.get(Payment, payment_id)


def save_payment(
    session: Session,
    payment: Payment,
) -> Payment:
    session.commit()
    session.refresh(payment)

    return payment