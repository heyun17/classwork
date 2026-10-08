from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Attendance, ClassModel, Payment, Student


STUDENT_NAMES: list[str] = [
    "김민준", "이서윤", "박지호", "최하윤", "정도윤",
    "강지우", "조예준", "윤서아", "장현우", "임수아",
    "한지민", "오준서", "서유진", "신민재", "권채원",
    "황도현", "안예린", "송시우", "전하린", "홍지훈",
    "김서준", "이채은", "박건우", "최유나", "정시윤",
    "강민서", "조우진", "윤지아", "장태윤", "임서현",
    "한준영", "오지유", "서민준", "신하은", "권도윤",
    "황서연", "안지호", "송예은", "전민혁", "홍수빈",
    "김현준", "이예나", "박시후", "최다은", "정우빈",
    "강채린", "조현서", "윤나연", "장준혁", "임가은",
    "한도윤", "오세아", "서정우", "신유림", "권민규",
    "황아린", "안준호", "송유진", "전시우", "홍서윤",
]

SCHOOLS: list[str] = [
    "한빛중학교",
    "새봄중학교",
    "푸른중학교",
    "미래중학교",
    "가온중학교",
    "한울중학교",
]


def get_count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def seed_classes(session: Session) -> None:
    if get_count(session, ClassModel) > 0:
        return

    session.add_all(
        [
            ClassModel(class_id=1, class_name="중1반", grade=1, capacity=20),
            ClassModel(class_id=2, class_name="중2반", grade=2, capacity=20),
            ClassModel(class_id=3, class_name="중3반", grade=3, capacity=20),
        ]
    )
    session.commit()


def seed_students(session: Session) -> None:
    if get_count(session, Student) > 0:
        return

    students: list[Student] = []

    for index, name in enumerate(STUDENT_NAMES, start=1):
        grade: int = ((index - 1) // 20) + 1

        students.append(
            Student(
                student_id=index,
                name=name,
                grade=grade,
                school=SCHOOLS[(index - 1) % len(SCHOOLS)],
                guardian_phone=f"010-{1000 + index:04d}-{2000 + index:04d}",
                status="재원",
                class_id=grade,
            )
        )

    session.add_all(students)
    session.commit()


def seed_attendance(session: Session) -> None:
    if get_count(session, Attendance) > 0:
        return

    today: date = date.today()
    records: list[Attendance] = []

    for day_offset in range(7):
        attendance_date: date = today - timedelta(days=day_offset)

        for student_id in range(1, 61):
            value: int = student_id + day_offset

            if value % 13 == 0:
                status = "결석"
            elif value % 7 == 0:
                status = "지각"
            else:
                status = "출석"

            records.append(
                Attendance(
                    student_id=student_id,
                    attendance_date=attendance_date,
                    status=status,
                    note=None,
                )
            )

    session.add_all(records)
    session.commit()


def seed_payments(session: Session) -> None:
    if get_count(session, Payment) > 0:
        return

    today: date = date.today()
    billing_month: str = today.strftime("%Y-%m")
    payments: list[Payment] = []

    for student_id in range(1, 61):
        is_paid: bool = student_id % 7 != 0

        payments.append(
            Payment(
                student_id=student_id,
                billing_month=billing_month,
                amount=300000,
                status="납부" if is_paid else "미납",
                paid_at=today if is_paid else None,
            )
        )

    session.add_all(payments)
    session.commit()


def main() -> None:
    with SessionLocal() as session:
        seed_classes(session)
        seed_students(session)
        seed_attendance(session)
        seed_payments(session)

        print(f"classes: {get_count(session, ClassModel)}")
        print(f"students: {get_count(session, Student)}")
        print(f"attendance: {get_count(session, Attendance)}")
        print(f"payments: {get_count(session, Payment)}")


if __name__ == "__main__":
    main()