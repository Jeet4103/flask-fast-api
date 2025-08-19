from pydantic import BaseModel, validator , EmailStr 
from email_validator import validate_email , EmailNotValidError
from db_manage.db_config import get_connection
from typing import Optional, List 
from enum import Enum
from datetime import date,datetime
from fastapi import UploadFile 
from decimal import Decimal
    
class  Permission(BaseModel):
    delete_students: bool
    soft_delete: bool
    update_student: bool
    advanced_search: bool
    bulk_register:bool
    create_parent:bool
    enrollment:bool
    create_courses:bool
    create_grades:bool
    create_attendance:bool
    student_document:bool
    student_fees:bool
    create_fees:bool

class Profile(BaseModel):
    phone_number: Optional[int] = None
    mothers_name: Optional[str] = None
    fathers_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    branch: Optional[str] = None
    status: Optional[str] = None
    designation: Optional[str] = None

    def dict(self, **kwargs):
        data = super().dict(**kwargs)
        if data['role'] == 'student':
            data.pop('designation', None)
        return data
    
class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"
  
class UserIn(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: EmailStr
    username: str
    password: str
    role:str

    @validator('email')
    def validate_email_format(cls, value):
        try:
            valid = validate_email(value)
            return valid.normalized  
        except EmailNotValidError as err:
            raise ValueError(str(err))
        
class studentInfo(BaseModel):
    phone_number: Optional[int] = None
    mothers_name: Optional[str] = None
    fathers_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    branch: Optional[str] = None
    status: Optional[str] = None

class staffInfo(BaseModel):
    phone_number: Optional[int] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    branch: Optional[str] = None
    designation: Optional[str] = None
    
class UserOut(BaseModel):
    id: int
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    student_info: Optional[studentInfo] = None
    staff_info: Optional[staffInfo] = None
    role: Optional[str] = None
    access_token: Optional[Token]
    
class Message(BaseModel):
    id: int
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None

class MessageResponse(BaseModel):
    users:List[UserOut]
 
class StudentLogin(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user:StudentLogin
    token: Token  

class StudentResponse(BaseModel):
    id: int
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    student_info: Optional[studentInfo] = None
    staff_info: Optional[staffInfo] = None
    role: Optional[str] = None

    def dict(self, **kwargs):
        data = super().dict(**kwargs)
        if data['role'] == 'staff':
            data.pop('student_info', None)
        else:
            data.pop('staff_info', None)
        return data

class UpdateMessageResponse(BaseModel):
    message:str

class SearchResponse(BaseModel):
    users:List[StudentResponse]

class UpdateStudent(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    
    student_info: Optional[studentInfo] = None
    staff_info: Optional[staffInfo] = None


class SortField(str, Enum):
    id = "id"
    first_name = "first_name"
    last_name = "last_name"
    email = "email"
    username = "username"
    full_name = "full_name" 
    phone_number = "phone_number"
    mothers_name = "mothers_name"
    fathers_name = "fathers_name"
    date_of_birth = "date_of_birth"
    address = "address"
    branch = "branch"
    designation = "designation"

class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"

class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    branch: str

class CourseOut(BaseModel):
    id: Optional[int] 
    name: Optional[str]
    description: Optional[str]
    branch: Optional[str]

class EnrollmentCreate(BaseModel):
    course: int

class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    course_id: int
    course_name: str    

class Email(BaseModel):
    email: List[EmailStr]

class EmailResponse(BaseModel):
    message: str
    name : str

class ParentContactCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: Optional[int] = None
    email: Optional[EmailStr] = None
    relationship: str
    address: Optional[str] = None   
    full_name: Optional[str] = None

class grades(BaseModel):
    student_id: int
    course_id: int
    term_id: Optional[int] = None
    marks_obtained: Optional[float] = None
    total_marks: Optional[float] = None

class GradesOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    course_id: int
    course_name: str
    term_id: Optional[int] = None
    term_name: Optional[str] = None
    grade: Optional[str] = None
    marks_obtained: Optional[float] = None
    total_marks: Optional[float] = None
    gpa: Optional[float] = None
    
class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: str

class AttendanceOut(BaseModel):
    id: int
    student_id: int
    date: date
    status: str
    created_at: datetime    
    updated_at: datetime

class FeesCategory(BaseModel):
    name: str
    amount: float
    description: Optional[str] = None

class StudentFee(BaseModel):
    fee_category_id: int
    student_id: int
    due_amount: float
    due_date: Optional[date] = None
    
class StudentFeeUpdate(BaseModel):
    id: int
    fee_category_id: Optional[int] = None
    total_amount: Optional[float] = None
    due_amount: Optional[float] = None
    due_date: Optional[date] = None
    status: Optional[str] = None

class payments(BaseModel):
    amount_paid: float
    payment_method: str
    fee_category_id: int

class PaymentOut(BaseModel):
    id: int
    student_fee_id: int
    amount_paid: float
    payment_method: str
    payment_date: date    
    receipt_number: str

class paymentsdetails(BaseModel):                                                               
    id: int
    amount_paid: Decimal
    payment_method: str
    payment_date: date
    receipt_number: str
    full_name: str
    status: str
