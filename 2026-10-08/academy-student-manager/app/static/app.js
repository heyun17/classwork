const dashboardSection =
    document.getElementById("dashboard-section");

const studentsSection =
    document.getElementById("students-section");

const attendanceSection =
    document.getElementById("attendance-section");

const paymentsSection =
    document.getElementById("payments-section");


const dashboardButton =
    document.getElementById("dashboard-button");

const studentsButton =
    document.getElementById("students-button");

const attendanceButton =
    document.getElementById("attendance-button");

const paymentsButton =
    document.getElementById("payments-button");


const studentListView =
    document.getElementById("student-list-view");

const studentDetailView =
    document.getElementById("student-detail-view");

const studentBackButton =
    document.getElementById("student-back-button");


function showSection(section) {
    dashboardSection.classList.add("hidden");
    studentsSection.classList.add("hidden");
    attendanceSection.classList.add("hidden");
    paymentsSection.classList.add("hidden");

    section.classList.remove("hidden");
}


async function loadDashboard() {
    const response = await fetch("/api/dashboard");

    if (!response.ok) {
        console.error("대시보드 조회 실패");
        return;
    }

    const data = await response.json();

    document.getElementById("total-students").textContent =
        data.total_students;

    document.getElementById("grade-1").textContent =
        data.grade_1_students;

    document.getElementById("grade-2").textContent =
        data.grade_2_students;

    document.getElementById("grade-3").textContent =
        data.grade_3_students;

    document.getElementById("today-present").textContent =
        data.today_present;

    document.getElementById("today-late").textContent =
        data.today_late;

    document.getElementById("today-absent").textContent =
        data.today_absent;

    document.getElementById("monthly-paid").textContent =
        data.monthly_paid;

    document.getElementById("monthly-unpaid").textContent =
        data.monthly_unpaid;
}


async function loadStudents(classId = "") {
    let url = "/api/students";

    if (classId !== "") {
        url += `?class_id=${classId}`;
    }

    const response = await fetch(url);

    if (!response.ok) {
        console.error("학생 목록 조회 실패");
        return;
    }

    const students = await response.json();

    const tableBody =
        document.getElementById("students-table-body");

    tableBody.innerHTML = "";

    for (const student of students) {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${student.student_id}</td>
            <td>${student.name}</td>
            <td>중${student.grade}</td>
            <td>${student.school}</td>
            <td>${student.status}</td>
        `;

        row.addEventListener("click", () => {
            loadStudentDetail(student.student_id);
        });

        tableBody.appendChild(row);
    }
}


async function loadStudentDetail(studentId) {
    const response =
        await fetch(`/api/students/${studentId}`);

    if (!response.ok) {
        console.error("학생 상세 조회 실패");
        return;
    }

    const data = await response.json();
    const student = data.student;

    document.getElementById("detail-name").textContent =
        student.name;

    document.getElementById("detail-grade").textContent =
        `중${student.grade}`;

    document.getElementById("detail-school").textContent =
        student.school;

    document.getElementById("detail-class").textContent =
        `중${student.class_id}반`;

    document.getElementById("detail-phone").textContent =
        student.guardian_phone;


    const attendanceList =
        document.getElementById("detail-attendance");

    attendanceList.innerHTML = "";

    for (const attendance of data.recent_attendance) {
        const item = document.createElement("li");

        item.textContent =
            `${attendance.attendance_date} - ${attendance.status}`;

        attendanceList.appendChild(item);
    }


    const paymentElement =
        document.getElementById("detail-payment");

    if (data.current_payment === null) {
        paymentElement.textContent = "수납 정보 없음";
    } else {
        paymentElement.textContent =
            `${data.current_payment.billing_month} / ` +
            `${data.current_payment.amount.toLocaleString()}원 / ` +
            `${data.current_payment.status}`;
    }


    studentListView.classList.add("hidden");
    studentDetailView.classList.remove("hidden");
}


async function loadAttendance() {
    const date =
        document.getElementById("attendance-date").value;

    const classId =
        document.getElementById("attendance-class").value;

    const message =
        document.getElementById("attendance-message");

    message.textContent = "";

    if (date === "") {
        message.textContent = "날짜를 선택하세요.";
        return;
    }


    const studentsResponse =
        await fetch(`/api/classes/${classId}/students`);

    const attendanceResponse =
        await fetch(
            `/api/attendance?date=${date}&class_id=${classId}`
        );


    if (
        !studentsResponse.ok ||
        !attendanceResponse.ok
    ) {
        message.textContent =
            "출결 정보를 불러오지 못했습니다.";

        return;
    }


    const students =
        await studentsResponse.json();

    const attendanceRecords =
        await attendanceResponse.json();


    const attendanceMap = new Map();

    for (const record of attendanceRecords) {
        attendanceMap.set(
            record.student_id,
            record
        );
    }


    const tableBody =
        document.getElementById("attendance-table-body");

    tableBody.innerHTML = "";


    for (const student of students) {
        const record =
            attendanceMap.get(student.student_id);

        const row =
            document.createElement("tr");

        const currentStatus =
            record ? record.status : "미등록";


        row.innerHTML = `
            <td>${student.student_id}</td>
            <td>${student.name}</td>
            <td>${student.school}</td>
            <td>${currentStatus}</td>
            <td class="attendance-actions"></td>
        `;


        const actionCell =
            row.querySelector(".attendance-actions");


        for (const status of ["출석", "지각", "결석"]) {
            const button =
                document.createElement("button");

            button.textContent = status;

            button.className =
                "attendance-action-button";

            if (record) {
                button.disabled = true;
            } else {
                button.addEventListener(
                    "click",
                    async () => {
                        await createAttendance(
                            student.student_id,
                            date,
                            status
                        );
                    }
                );
            }

            actionCell.appendChild(button);
        }


        tableBody.appendChild(row);
    }
}


async function createAttendance(
    studentId,
    attendanceDate,
    status
) {
    const response = await fetch(
        "/api/attendance",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                student_id: studentId,
                attendance_date: attendanceDate,
                status: status,
                note: null
            })
        }
    );


    const message =
        document.getElementById("attendance-message");


    if (response.status === 201) {
        message.textContent =
            `${studentId}번 학생 출결 등록 완료`;

        await loadAttendance();
        await loadDashboard();

        return;
    }


    const error = await response.json();

    message.textContent =
        error.detail ?? "출결 등록 실패";
}


async function loadPayments() {
    const month =
        document.getElementById("payment-month").value;

    const status =
        document.getElementById("payment-status").value;

    const classId =
        document.getElementById("payment-class").value;

    const message =
        document.getElementById("payment-message");

    message.textContent = "";

    if (month === "") {
        message.textContent = "대상 월을 선택하세요.";
        return;
    }


    const paymentParams = new URLSearchParams();

    paymentParams.set("month", month);

    if (status !== "") {
        paymentParams.set("status", status);
    }

    if (classId !== "") {
        paymentParams.set("class_id", classId);
    }


    const studentParams = new URLSearchParams();

    if (classId !== "") {
        studentParams.set("class_id", classId);
    }


    const paymentUrl =
        `/api/payments?${paymentParams.toString()}`;

    const studentUrl =
        studentParams.toString() === ""
            ? "/api/students"
            : `/api/students?${studentParams.toString()}`;


    const paymentsResponse =
        await fetch(paymentUrl);

    const studentsResponse =
        await fetch(studentUrl);


    if (
        !paymentsResponse.ok ||
        !studentsResponse.ok
    ) {
        message.textContent =
            "수납 정보를 불러오지 못했습니다.";

        return;
    }


    const payments =
        await paymentsResponse.json();

    const students =
        await studentsResponse.json();


    const studentMap = new Map();

    for (const student of students) {
        studentMap.set(
            student.student_id,
            student
        );
    }


    const tableBody =
        document.getElementById("payments-table-body");

    tableBody.innerHTML = "";


    for (const payment of payments) {
        const student =
            studentMap.get(payment.student_id);

        if (!student) {
            continue;
        }


        const row =
            document.createElement("tr");


        const paidAt =
            payment.paid_at ?? "-";


        row.innerHTML = `
            <td>${student.student_id}</td>
            <td>${student.name}</td>
            <td>중${student.grade}</td>
            <td>중${student.class_id}반</td>
            <td>${payment.billing_month}</td>
            <td>${payment.amount.toLocaleString()}원</td>
            <td>${payment.status}</td>
            <td>${paidAt}</td>
            <td class="payment-action"></td>
        `;


        const actionCell =
            row.querySelector(".payment-action");

        const button =
            document.createElement("button");

        button.className =
            "payment-action-button";


        if (payment.status === "미납") {
            button.textContent = "납부 처리";

            button.addEventListener(
                "click",
                async () => {
                    await markPaymentPaid(
                        payment.payment_id
                    );
                }
            );
        } else {
            button.textContent = "납부 완료";
            button.disabled = true;
        }


        actionCell.appendChild(button);

        tableBody.appendChild(row);
    }


    if (payments.length === 0) {
        message.textContent =
            "조건에 해당하는 수납 정보가 없습니다.";
    }
}


async function markPaymentPaid(paymentId) {
    const response = await fetch(
        `/api/payments/${paymentId}`,
        {
            method: "PATCH"
        }
    );


    const message =
        document.getElementById("payment-message");


    if (response.ok) {
        const payment =
            await response.json();

        message.textContent =
            `${payment.student_id}번 학생 납부 처리 완료`;

        await loadPayments();
        await loadDashboard();

        return;
    }


    const error =
        await response.json();

    message.textContent =
        error.detail ?? "납부 처리 실패";
}


dashboardButton.addEventListener(
    "click",
    () => {
        showSection(dashboardSection);
        loadDashboard();
    }
);


studentsButton.addEventListener(
    "click",
    () => {
        showSection(studentsSection);

        studentDetailView.classList.add("hidden");
        studentListView.classList.remove("hidden");

        loadStudents();
    }
);


attendanceButton.addEventListener(
    "click",
    () => {
        showSection(attendanceSection);
        loadAttendance();
    }
);


paymentsButton.addEventListener(
    "click",
    () => {
        showSection(paymentsSection);
        loadPayments();
    }
);


studentBackButton.addEventListener(
    "click",
    () => {
        studentDetailView.classList.add("hidden");
        studentListView.classList.remove("hidden");
    }
);


document
    .querySelectorAll(
        ".filter-buttons button[data-class-id]"
    )
    .forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                const classId =
                    button.dataset.classId;

                studentDetailView
                    .classList
                    .add("hidden");

                studentListView
                    .classList
                    .remove("hidden");

                loadStudents(classId);
            }
        );
    });


document
    .getElementById("attendance-search-button")
    .addEventListener(
        "click",
        () => {
            loadAttendance();
        }
    );


document
    .getElementById("payment-search-button")
    .addEventListener(
        "click",
        () => {
            loadPayments();
        }
    );


const today =
    new Date().toISOString().slice(0, 10);

document.getElementById(
    "attendance-date"
).value = today;


const currentMonth =
    new Date().toISOString().slice(0, 7);

document.getElementById(
    "payment-month"
).value = currentMonth;


loadDashboard();