from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine, get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student

SECRET_KEY = "change-this-secret-key-before-deployment"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hasher = PasswordHash.recommended()

security = HTTPBearer()

app = FastAPI(
    title="Student Course Management API",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)


class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr
    department: str
    year: int
    password: str = Field(min_length=8)


class StudentResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    department: str
    year: int
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CourseCreate(BaseModel):
    code: str
    title: str
    description: str | None = None
    capacity: int = 30


class CourseResponse(BaseModel):
    id: int
    code: str
    title: str
    description: str | None
    capacity: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    status: str
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    stored_hash: str,
) -> bool:
    return password_hasher.verify(
        plain_password,
        stored_hash,
    )


def create_access_token(student_id: int) -> str:
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return jwt.encode(
        {
            "sub": str(student_id),
            "exp": expires_at,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    invalid_token_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        student_id = int(payload.get("sub"))

    except (JWTError, TypeError, ValueError):
        raise invalid_token_error

    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if not student or not student.is_active:
        raise invalid_token_error

    return student


def require_admin(
    current_student: Student = Depends(get_current_student),
):
    if current_student.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_student


def create_default_admin():
    db = SessionLocal()

    try:
        admin = (
            db.query(Student)
            .filter(Student.email == "admin@courseapi.com")
            .first()
        )

        if not admin:
            admin = Student(
                full_name="System Administrator",
                email="admin@courseapi.com",
                department="Administration",
                year=1,
                password_hash=hash_password("Admin@123"),
                role="admin",
            )

            db.add(admin)
            db.commit()

    finally:
        db.close()


create_default_admin()


@app.get("/")
def home():
    return {
        "message": "Student Course Management API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
):
    existing_student = (
        db.query(Student)
        .filter(Student.email == student.email)
        .first()
    )

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="A student with this email already exists",
        )

    new_student = Student(
        full_name=student.full_name,
        email=student.email,
        department=student.department,
        year=student.year,
        password_hash=hash_password(student.password),
        role="student",
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


@app.get(
    "/students",
    response_model=list[StudentResponse],
)
def get_all_students(
    db: Session = Depends(get_db),
    _: Student = Depends(require_admin),
):
    return db.query(Student).all()


@app.post("/auth/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    student = (
        db.query(Student)
        .filter(Student.email == login_data.email)
        .first()
    )

    if not student or not verify_password(
        login_data.password,
        student.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return {
        "access_token": create_access_token(student.id),
        "token_type": "bearer",
    }


@app.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    _: Student = Depends(require_admin),
):
    existing_course = (
        db.query(Course)
        .filter(Course.code == course.code.upper())
        .first()
    )

    if existing_course:
        raise HTTPException(
            status_code=400,
            detail="A course with this code already exists",
        )

    new_course = Course(
        code=course.code.upper(),
        title=course.title,
        description=course.description,
        capacity=course.capacity,
    )

    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    return new_course


@app.get("/courses", response_model=list[CourseResponse])
def get_all_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()


@app.post(
    "/enrollments",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    enrollment: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    course = (
        db.query(Course)
        .filter(Course.id == enrollment.course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == current_student.id,
            Enrollment.course_id == enrollment.course_id,
        )
        .first()
    )

    if existing_enrollment:
        raise HTTPException(
            status_code=400,
            detail="Student is already enrolled in this course",
        )

    enrolled_count = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == enrollment.course_id,
            Enrollment.status == "enrolled",
        )
        .count()
    )

    if enrolled_count >= course.capacity:
        raise HTTPException(
            status_code=400,
            detail="Course is full",
        )

    new_enrollment = Enrollment(
        student_id=current_student.id,
        course_id=enrollment.course_id,
        status="enrolled",
    )

    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)

    return new_enrollment


@app.get(
    "/enrollments/me",
    response_model=list[EnrollmentResponse],
)
def get_my_enrollments(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    return (
        db.query(Enrollment)
        .filter(Enrollment.student_id == current_student.id)
        .all()
    )


@app.get(
    "/enrollments",
    response_model=list[EnrollmentResponse],
)
def get_all_enrollments(
    db: Session = Depends(get_db),
    _: Student = Depends(require_admin),
):
    return db.query(Enrollment).all()