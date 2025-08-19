from db_manage.db_config import get_connection
from fastapi import FastAPI , HTTPException , status , Depends ,UploadFile ,File ,APIRouter ,Query
from fastapi.responses import FileResponse
from validation import *
import uvicorn  
from typing import List, Optional
from auth.auth import create_access_token, decode_token 
from auth.hash import hash_password, verify_password
from fastapi.security import HTTPBearer 
from fastapi.responses import JSONResponse
from fastapi_mail import FastMail , MessageSchema , ConnectionConfig 
import pandas as pd
import os
import zipfile
from decimal import Decimal
from starlette.background import BackgroundTasks

app = FastAPI(debug=True)

attendance_router = APIRouter(prefix="/attendance", tags=["Attendance"])
course_router = APIRouter(prefix="/course", tags=["Courses"])
grades_router = APIRouter(prefix="/grades", tags=["Grades"])
students_router = APIRouter(prefix="/student", tags=["Students"])
fees_router = APIRouter(prefix="/fees", tags=["Fees"])

oauth2_scheme = HTTPBearer()

conf = ConnectionConfig(
    MAIL_USERNAME="jeetpatel4103@gmail.com",
    MAIL_PASSWORD="becp zowj egqq onno",  
    MAIL_FROM="jeetpatel4103@email.com",
    MAIL_FROM_NAME="Students Management System",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_mail(email: Email,name: str):

    template = f"""
        <html>
        <body>
        

         <p>Hi {name}!! <br>
        <br>You successfully registered to the system. </p>
        <br>Thanks for regisrtaration to the student management system. </p>
        </body>
        </html>
        """
    message = MessageSchema(
        subject="Registration Successful",
        recipients=[email], 
        body=template,
        subtype="html"
        )
    fm = FastMail(conf)
    await fm.send_message(message)

    return JSONResponse(status_code=200, content={"message": "email has been sent"})

def _generate_full_name(first_name: str, middle_name:Optional[str] = None, last_name:Optional[str] = None) -> str:
  parts = [first_name, middle_name, last_name]
  full_name = ' '.join(str(part).strip() for part in parts if part)
  return full_name.strip()

def _get_user_permissions(user_id: int) -> Permission:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM permissions WHERE user_id = %s", (user_id,))
    permissions = cursor.fetchone()
    cursor.close()
    conn.close()
    if not permissions:
        raise HTTPException(status_code=404, detail="User not found")
    return Permission(**permissions)

def calculate_grade(marks_obtained: float, total_marks: float) -> str:
    if total_marks == 0:
        return "N/A"
    percentage = (marks_obtained / total_marks) * 100

    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"

@app.exception_handler(HTTPException)
def http_exception_handler(request, exc):
    if exc.status_code == status.HTTP_403_FORBIDDEN and exc.detail == "Not authenticated":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": "Access denied!"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
 
@app.get('/health')
def health_check(token: str=Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
          raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTp_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
           raise HTTPException(status_code=401, detail="Invalid token payload")
        conn = get_connection()
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
 
@app.post('/student/register', response_model=List[Message], status_code=status.HTTP_201_CREATED)
async def register_student(user_list: List[UserIn]):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        registered_users = []

        for user in user_list:
            full_name_value = _generate_full_name(user.first_name, user.middle_name, user.last_name)
            
            cursor.execute(
                "SELECT * FROM users WHERE email = %s OR username =%s",
                (user.email, user.username)
            )
            if cursor.fetchone():
                cursor.close()
                conn.close()
                raise HTTPException(status_code=400, detail="Email or username already exists")

            hashed_password = hash_password(user.password)

            cursor.execute(
                "INSERT INTO users (username, password, email, role, first_name, middle_name, last_name, full_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (user.username.strip(), hashed_password.strip(), user.email.strip(), user.role.strip(), user.first_name.strip(), user.middle_name.strip() if user.middle_name else None, user.last_name.strip() if user.last_name else None, full_name_value)
            )
            user_id = cursor.lastrowid

            if user.role == 'staff':
             cursor.execute(
                 "INSERT INTO staff (user_id, first_name, middle_name, last_name) VALUES (%s, %s, %s, %s)",
                 (user_id, user.first_name.strip(), user.middle_name.strip() if user.middle_name else None, user.last_name.strip() if user.last_name else None)
             )
             await send_mail(user.email,full_name_value)
            elif user.role == 'student':
             cursor.execute(
                 "INSERT INTO students (user_id, first_name, middle_name, last_name) VALUES (%s, %s, %s, %s)",
                 (user_id, user.first_name.strip(), user.middle_name.strip() if user.middle_name else None, user.last_name.strip() if user.last_name else None)
             )
             await send_mail(user.email,full_name_value)
        registered_users.append({  
        "id": user_id,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "full_name": full_name_value,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        })
       
        conn.commit()
        cursor.close()
        conn.close()

        return registered_users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Student Registration Failed: {str(e)}")
    
@app.post('/student/bulk-register', response_model=UpdateMessageResponse, status_code=status.HTTP_201_CREATED,tags=["Students"])
async def bulk_register_student(file:UploadFile = File(...),token:str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        permission = _get_user_permissions(payload.get("sub"))
        if not permission.bulk_register:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        if not file.filename.endswith(('.csv', '.xls', '.xlsx')):
            raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)

        required_columns = {"first_name", "last_name", "middle_name", "email", "username", "password", "role"}
        if not required_columns.issubset(set(df.columns)):
            raise HTTPException(status_code=400, detail="Invalid file format")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)   

        inserted_users = 0
        skipped_emails = []

        for _, row in df.iterrows():
            email = str(row['email']).strip()
        
            cursor.execute("SELECT * FROM users WHERE email = %s ",
                           ((email,))
            )
            if cursor.fetchone():
              skipped_emails.append(email)
              continue 

            hashed_password = hash_password(row['password'])
            full_name = _generate_full_name(row['first_name'], row['middle_name'], row['last_name'])
            cursor.execute("INSERT INTO users (username, password, email, role, first_name, middle_name, last_name, full_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (row['username'], hashed_password, email, row['role'], row['first_name'], row['middle_name'], row['last_name'], full_name)
            )
            user_id = cursor.lastrowid
    
            if row['role'] == 'staff':
                cursor.execute("INSERT INTO staff (user_id, first_name, middle_name, last_name) VALUES (%s, %s, %s, %s)",
                               (user_id, row['first_name'], row['middle_name'], row['last_name'])
                )
                await send_mail(email,full_name)
            elif row['role'] == 'student':
                cursor.execute("INSERT INTO students (user_id, first_name, middle_name, last_name) VALUES (%s, %s, %s, %s)",
                               (user_id, row['first_name'], row['middle_name'], row['last_name'])
                )
                await send_mail(email,full_name)
            inserted_users += 1

        conn.commit()
        cursor.close()
        conn.close()
        return {"message": f"Successfully inserted {inserted_users} users"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk Registration Failed: {str(e)}")



@app.post('/student/login', response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_student(user: StudentLogin):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s and is_active = 1", (user.username,))
        existing_student = cursor.fetchone()
        if not existing_student or not verify_password(user.password, existing_student['password']):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        token = create_access_token(data={"sub": str(existing_student['id'])})
        return {
            "user": existing_student,
            "token": {
                "access_token": token,
                "token_type": "bearer"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Login Failed: " + str(e))

@app.get("/logedin/student", response_model=StudentResponse,tags=["Students"])
def get_logedin_student(token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s and is_active = 1", (user_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.get("role") == "student":
            cursor.execute("""
                 SELECT s.user_id,s.first_name, s.middle_name, s.last_name, si.phone_number, si.mothers_name, si.fathers_name, si.date_of_birth, si.address, si.branch
                 FROM students s
                 LEFT JOIN student_info si ON s.user_id = si.student_id
                 WHERE s.user_id = %s;
            """, (user_id,))
            current_user = cursor.fetchone()

            user_response = {
                "id": user_id,
                "first_name": user.get("first_name"),
                "middle_name": user.get("middle_name"),
                "last_name": user.get("last_name"),
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "username": user.get("username"),
                "role": "student",
                "student_info": {
                    "phone_number": current_user.get("phone_number"),
                    "mothers_name": current_user.get("mothers_name"),
                    "fathers_name": current_user.get("fathers_name"),
                    "date_of_birth": current_user.get("date_of_birth"),
                    "address": current_user.get("address"),
                    "branch": current_user.get("branch")
                }
            }

        elif user.get("role") == "staff":
            cursor.execute("""
                 SELECT s.user_id, s.first_name, s.middle_name, s.last_name, 
                        si.phone_number, si.date_of_birth, si.address, si.branch, si.designation
                 FROM staff s
                 LEFT JOIN staff_info si ON s.user_id = si.staff_id
                 WHERE s.user_id = %s
            """, (user_id,))
            current_user = cursor.fetchone()

            user_response = {
                "id": user_id,
                "first_name": user.get("first_name"),
                "middle_name": user.get("middle_name"),
                "last_name": user.get("last_name"),
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "username": user.get("username"),
                "role": "staff",
                "staff_info": {
                    "phone_number": current_user.get("phone_number"),
                    "date_of_birth": current_user.get("date_of_birth"),
                    "address": current_user.get("address"),
                    "branch": current_user.get("branch"),
                    "designation": current_user.get("designation")
                }
            }

        cursor.close()
        conn.close()

        return user_response  

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   
@app.get('/students/', response_model=List[StudentResponse], status_code=status.HTTP_200_OK,tags=["Students"])
def get_all_users(token: str=Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
           raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
          raise HTTPException(
        status_code=status.HTTp_401_UNAUTHORIZED,
        detail="Invalid token provided"
        )
        student_id = payload.get("sub")
        if not student_id:
           raise HTTPException(status_code=401, detail="Invalid token payload")
        permission = _get_user_permissions(student_id)
        if not permission.advanced_search:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM USERS WHERE IS_ACTIVE = 1")
        Users = cursor.fetchall()
        users = []
        
        for user in Users:
            if user['role'] == 'student':
                cursor.execute("""
                 SELECT s.user_id,s.first_name, s.middle_name, s.last_name, si.phone_number, si.mothers_name, si.fathers_name, si.date_of_birth, si.address, si.branch
                 FROM students s
                 LEFT JOIN student_info si ON s.user_id = si.student_id
                 WHERE s.user_id = %s;
                """, (user['id'],))
                student = cursor.fetchone()
                if student:
                    users.append({
                        'id': student['user_id'],
                        'first_name': student['first_name'],
                        'middle_name': student['middle_name'],
                        'last_name': student['last_name'],
                        'full_name': user['full_name'],
                        'email': user['email'],
                        'username': user['username'],
                        'role': 'student',
                        'student_info': {
                            'phone_number': student['phone_number'],
                            'mothers_name': student['mothers_name'],
                            'fathers_name': student['fathers_name'],
                            'date_of_birth': student['date_of_birth'],
                            'address': student['address'],
                            'branch': student['branch']
                        }
                    })
        
            elif user['role'] == 'staff':
                cursor.execute("""
                 SELECT s.user_id, s.first_name, s.middle_name, s.last_name, 
                        si.phone_number, si.date_of_birth, si.address, si.branch, si.designation
                 FROM staff s
                 LEFT JOIN staff_info si ON s.user_id = si.staff_id
                 WHERE s.user_id = %s
                """, (user['id'],))
                staff = cursor.fetchone()
                if staff:
                    users.append({
                        'id': staff['user_id'],
                        'first_name': staff['first_name'],
                        'middle_name': staff['middle_name'],
                        'last_name': staff['last_name'],
                        'full_name': user['full_name'],
                        'email': user['email'],
                        'username': user['username'],
                        'role': 'staff',
                        'staff_info': {
                            'phone_number': staff['phone_number'],
                            'date_of_birth': staff['date_of_birth'],
                            'address': staff['address'],
                            'branch': staff['branch'],
                            'designation': staff['designation']
                        }
                    })
        return users
    except HTTPException as e:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
  
@app.get('/student/{id}', response_model=StudentResponse,tags=["Students"])
def get_student_by_id(id: int,token: str=Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        permission = _get_user_permissions(student_id)
        if not permission.update_student:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        conn = get_connection() 
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = 1", (id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.get("role") == "student":
            cursor.execute("""
                 SELECT s.user_id,s.first_name, s.middle_name, s.last_name, si.phone_number, si.mothers_name, si.fathers_name, si.date_of_birth, si.address, si.branch,si.status
                 FROM students s
                 LEFT JOIN student_info si ON s.user_id = si.student_id
                 WHERE s.user_id = %s;
            """, (id,))
            current_user = cursor.fetchone()

            user_response = {
                "id": id,
                "first_name": user.get("first_name"),
                "middle_name": user.get("middle_name"),
                "last_name": user.get("last_name"),
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "username": user.get("username"),
                "role": "student",
                "student_info": {
                    "phone_number": current_user.get("phone_number"),
                    "mothers_name": current_user.get("mothers_name"),
                    "fathers_name": current_user.get("fathers_name"),
                    "date_of_birth": current_user.get("date_of_birth"),
                    "address": current_user.get("address"),
                    "branch": current_user.get("branch"),
                    "status": current_user.get("status")
                }
            }

        elif user.get("role") == "staff":   
            cursor.execute("""
                 SELECT s.user_id, s.first_name, s.middle_name, s.last_name, 
                        si.phone_number, si.date_of_birth, si.address, si.branch, si.designation
                 FROM staff s
                 LEFT JOIN staff_info si ON s.user_id = si.staff_id
                 WHERE s.user_id = %s
            """, (id,))
            current_user = cursor.fetchone()

            user_response = {
                "id": id,
                "first_name": user.get("first_name"),
                "middle_name": user.get("middle_name"),
                "last_name": user.get("last_name"),
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "username": user.get("username"),
                "role": "staff",
                "staff_info": {
                    "phone_number": current_user.get("phone_number"),
                    "date_of_birth": current_user.get("date_of_birth"),
                    "address": current_user.get("address"),
                    "designation": current_user.get("designation"),
                    "branch": current_user.get("branch")
                }
            }
    

        cursor.close()
        conn.close()
        if not user:
            raise HTTPException(status_code=404, detail="Student not found")

        return user_response
    except HTTPException as e:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

@app.delete('/student/{id}', response_model=UpdateMessageResponse, status_code=status.HTTP_200_OK,tags=["Students"])
def soft_delete_student(id: int, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
           raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
          raise HTTPException(
        status_code=status.HTTp_401_UNAUTHORIZED,
        detail="Invalid token provided"
        )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        permission = _get_user_permissions(student_id)

        if not permission.delete_students:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s and is_active = 1", (id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found or already Updated")
        cursor.execute("UPDATE users SET is_active = 0 WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Student deleted successfully"}
    except HTTPException as e:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete('/delete/{id}',tags=["Students"])
def delete_student(id: int, token: str = Depends(oauth2_scheme)):    
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )

        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)

        if not permission.delete_students:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s and is_active = 1", (id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Student not found")
        
        cursor.execute("DELETE FROM users WHERE id = %s and is_active = 1", (id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Student deleted successfully"}
    
    except HTTPException as e:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Student Deletion Failed: " + str(e))

@app.post('/user/profile/', response_model=UpdateMessageResponse, status_code=status.HTTP_200_OK,tags=["Students"])
def update_user_profile(request: Profile, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = 1", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found or inactive")
        
        role = user.get("role")
        
        if role == "student":
            cursor.execute(
                "INSERT INTO student_info (student_id, phone_number, mothers_name, fathers_name, date_of_birth, address, branch,status) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)",
                (user_id, request.phone_number, request.mothers_name, request.fathers_name, request.date_of_birth, request.address, request.branch,request.status)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return {"message": "Student profile updated successfully"}
        
        elif role == "staff":
            cursor.execute(
                "INSERT INTO staff_info (staff_id, phone_number, date_of_birth, address, branch, designation) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, request.phone_number, request.date_of_birth, request.address, request.branch, request.designation)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return {"message": "Staff profile updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch('/user/update/{id}', response_model=StudentResponse,tags=["Students"])
def update_user(id: int, request: UpdateStudent, token: str = Depends(oauth2_scheme)):
    try:

        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(status_code=401, detail="Invalid token provided")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(user_id)
        if not permission.soft_delete:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = 1", (id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found or inactive")

        role = user.get("role")
        email = request.email or user["email"]
        username = request.username or user["username"]

        if role == "student":
            cursor.execute("""
                SELECT s.id AS student_id, s.first_name, s.middle_name, s.last_name,
                       si.phone_number, si.mothers_name, si.fathers_name,
                       si.date_of_birth, si.address, si.branch, si.status
                FROM students s
                LEFT JOIN student_info si ON s.user_id = si.student_id
                WHERE s.user_id = %s
            """, (id,))
            student = cursor.fetchone()
            if not student:
                raise HTTPException(status_code=404, detail="Student data not found")    

            first_name = request.first_name or student["first_name"]
            middle_name = request.middle_name or student["middle_name"]
            last_name = request.last_name or student["last_name"]
            full_name = _generate_full_name(first_name, middle_name, last_name)
            phone_number = request.student_info.phone_number if request.student_info and request.student_info.phone_number else student["phone_number"]
            mothers_name = request.student_info.mothers_name if request.student_info and request.student_info.mothers_name else student["mothers_name"]
            fathers_name = request.student_info.fathers_name if request.student_info and request.student_info.fathers_name else student["fathers_name"]
            status = request.student_info.status if request.student_info and request.student_info.status else student["status"]
            date_of_birth = request.student_info.date_of_birth if request.student_info and request.student_info.date_of_birth else student["date_of_birth"]
            address = request.student_info.address if request.student_info and request.student_info.address else student["address"]
            branch = request.student_info.branch if request.student_info and request.student_info.branch else student["branch"]

            full_name = _generate_full_name(first_name, middle_name, last_name)


            cursor.execute("UPDATE users SET first_name=%s, middle_name=%s, last_name=%s, email=%s, username=%s , full_name=%s WHERE id=%s",
                           (first_name, middle_name, last_name, email, username,full_name, id))
            cursor.execute("UPDATE students SET first_name=%s, middle_name=%s, last_name=%s WHERE user_id=%s",
                           (first_name, middle_name, last_name, id))
            cursor.execute("""
                UPDATE student_info 
                SET phone_number=%s, mothers_name=%s, fathers_name=%s,
                    date_of_birth=%s, address=%s, branch=%s, status=%s
                WHERE student_id=%s
            """, (phone_number, mothers_name, fathers_name, date_of_birth, address, branch, status, id))


        elif role == "staff":
            cursor.execute("""
                SELECT s.id AS staff_id, s.first_name, s.middle_name, s.last_name,
                       si.phone_number, si.designation,
                       si.date_of_birth, si.address
                FROM staff s
                LEFT JOIN staff_info si ON s.id = si.staff_id
                WHERE s.user_id = %s
            """, (id,))
            staff = cursor.fetchone()
            if not staff:
                raise HTTPException(status_code=404, detail="Staff data not found")

            first_name = request.first_name or staff["first_name"]
            middle_name = request.middle_name or staff["middle_name"]
            last_name = request.last_name or staff["last_name"]
            phone_number = request.staff_info.phone_number if request.staff_info and request.staff_info.phone_number else staff["phone_number"]
            designation = request.staff_info.designation if request.staff_info and request.staff_info.designation else staff["designation"]
            date_of_birth = request.staff_info.date_of_birth if request.staff_info and request.staff_info.date_of_birth else staff["date_of_birth"]
            address = request.staff_info.address if request.staff_info and request.staff_info.address else staff["address"]
            full_name = _generate_full_name(first_name, middle_name, last_name)
 
            cursor.execute("UPDATE users SET first_name=%s, middle_name=%s, last_name=%s, email=%s, username=%s WHERE id=%s",
                           (first_name, middle_name, last_name, email, username, id))
            cursor.execute("UPDATE staff SET first_name=%s, middle_name=%s, last_name=%s WHERE user_id=%s",
                           (first_name, middle_name, last_name, id))
            cursor.execute("""
                UPDATE staff_info SET phone_number=%s, designation=%s,
                                      date_of_birth=%s, address=%s
                WHERE staff_id=%s
            """, (phone_number, designation, date_of_birth, address, staff["staff_id"]))

        else:
            raise HTTPException(status_code=400, detail="Unsupported role")
        
        conn.commit()

        if role == "student":
            cursor.execute("""
                SELECT u.id, u.first_name, u.middle_name, u.last_name, u.email, u.username, 
                       u.full_name, u.role,
                       si.phone_number, si.mothers_name, si.fathers_name, si.date_of_birth, 
                       si.address, si.branch, si.status
                FROM users u
                JOIN students s ON s.user_id = u.id
                LEFT JOIN student_info si ON si.student_id = s.user_id
                WHERE u.id = %s
            """, (id,))
            updated = cursor.fetchone()
            updated["student_info"] = {
                "phone_number": updated.get("phone_number"),
                "mothers_name": updated.get("mothers_name"),
                "fathers_name": updated.get("fathers_name"),
                "date_of_birth": updated.get("date_of_birth"),
                "address": updated.get("address"),
                "branch": updated.get("branch"),
                "status": updated.get("status")
            }
            updated["staff_info"] = None

        elif role == "staff":
            cursor.execute("""
                SELECT u.id, u.first_name, u.middle_name, u.last_name, u.email, u.username, 
                       u.full_name, u.role,
                       si.phone_number, si.designation, si.date_of_birth, si.address
                FROM users u
                JOIN staff s ON s.user_id = u.id
                LEFT JOIN staff_info si ON si.staff_id = s.id
                WHERE u.id = %s
            """, (id,))
            updated = cursor.fetchone()
            updated["staff_info"] = {
                "phone_number": updated.pop("phone_number"),
                "designation": updated.pop("designation"),
                "date_of_birth": updated.pop("date_of_birth"),
                "address": updated.pop("address")
            }
            updated["student_info"] = None

        cursor.close()
        conn.close()
        return updated

    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/student/search/", response_model=SearchResponse,tags=["Students"])
def advanced_search(
    query: Optional[str] = None,
    sort_by: Optional[SortField] = SortField.id,
    sort_order: Optional[SortDirection] = SortDirection.asc,
    token: str=Depends(oauth2_scheme)
):
    try:
      token_str = token.credentials
      payload = decode_token(token_str)
      if not payload:
          raise HTTPException(status_code=401, detail="Invalid or expired token")
      if token.credentials != token_str:
          raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token provided"
        )
      student_id = payload.get("sub")
      if not student_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
      
      Permission = _get_user_permissions(student_id)
      if not Permission.advanced_search:
          raise HTTPException(status_code=403, detail="Not enough permissions")
      conn = get_connection()
      cursor = conn.cursor(dictionary=True)
      base_query = """
           SELECT 
               u.id, u.first_name, u.middle_name, u.last_name, u.full_name,
               u.email, u.username, u.role,    
               -- Student Info
               CAST(si.phone_number AS CHAR) AS student_phone,
               si.mothers_name,
               si.fathers_name,
               si.date_of_birth AS student_dob,
               si.branch AS student_branch,
               si.address AS student_address,
               -- Staff Info
               CAST(st.phone_number AS CHAR) AS staff_phone ,
               st.date_of_birth AS staff_dob,
               st.branch AS staff_branch,
               st.address AS staff_address,
               st.designation,    
               -- Student Courses
               sc.course_id as course_id,
               sc.course_name as course_name 

           FROM users u
           LEFT JOIN student_info si ON u.id = si.student_id
           LEFT JOIN staff_info st ON u.id = st.staff_id
           LEFT JOIN student_courses sc on u.id = sc.student_id
       """    
      params = []    
  
      if query:
        query_conditions = []
        like = f"%{query}%"
    
        if str(query).isdigit():
            query_conditions.append("u.id = %s")
            params.append(int(query))
    
        query_conditions.extend([
            "u.first_name LIKE %s",
            "u.middle_name LIKE %s",
            "u.last_name LIKE %s",
            "u.full_name LIKE %s",
            "u.email LIKE %s",
            "u.role LIKE %s",
            "u.username LIKE %s",
            "si.phone_number = %s",
            "si.mothers_name LIKE %s",
            "si.fathers_name LIKE %s",
            "si.branch LIKE %s",
            "si.address LIKE %s",
            "st.phone_number = %s",
            "st.branch LIKE %s",
            "st.address LIKE %s",
            "st.designation LIKE %s",
            "sc.course_name LIKE %s",
            "sc.course_id LIKE %s"
        ])
    
        base_query += "\nWHERE (" + "\n OR ".join(query_conditions) + ")"
    
        params.extend([
            like, like, like, like,
            like, like, like,
            query ,
            like, like, like, like,
            query ,  
            like, like, like,
            like, 
            like
        ])

      if sort_by and sort_order:
          base_query += f" ORDER BY u.{sort_by.value} {sort_order.value.upper()}"
      
      cursor.execute(base_query, params)
      results = cursor.fetchall()    
      users = []
      for row in results:
           user = {
               "id": row["id"],
               "first_name": row["first_name"],
               "middle_name": row.get("middle_name"),
               "last_name": row.get("last_name"),
               "full_name": row.get("full_name"),
               "email": row["email"],
               "username": row["username"],
               "role": row["role"],
           }    
           if row["role"] == "student":
               user["student_info"] = {
                   "phone_number": row.get("student_phone"),
                   "mothers_name": row.get("mothers_name"),
                   "fathers_name": row.get("fathers_name"),
                   "date_of_birth": row.get("student_dob"),
                   "branch": row.get("student_branch"),
                   "address": row.get("student_address")
               }
           elif row["role"] == "staff":
               user["staff_info"] = {
                   "phone_number": row.get("staff_phone"),
                   "date_of_birth": row.get("staff_dob"),
                   "branch": row.get("staff_branch"),
                   "address": row.get("staff_address"),
                   "designation": row.get("designation")
               }    
           users.append(user)    
      return {"users": users}  
    except HTTPException as e:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/create/course", response_model=CourseOut, status_code=status.HTTP_201_CREATED, tags=["Courses"])
def create_course(course: CourseCreate,token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:    
            raise HTTPException(status_code=401, detail="Invalid token payload")
        permission = _get_user_permissions(student_id)
        if not permission.create_courses:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM courses WHERE name = %s", (course.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Course already exists")
        
        cursor.execute(
            "INSERT INTO courses (name, description, branch, created_at) VALUES (%s, %s, %s, NOW())",
            (course.name, course.description, course.branch)
        )
        conn.commit()

        course_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return CourseOut(
            id=course_id,
            name=course.name,
            description=course.description,
            branch=course.branch
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/", response_model=List[CourseOut], status_code=status.HTTP_200_OK, tags=["Courses"])
def get_all_courses(token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)   
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()
        cursor.close()
        conn.close()
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/student/enrollment/", response_model=List[EnrollmentOut], status_code=status.HTTP_200_OK, tags=["Courses"])
def enroll_student(enrollment: EnrollmentCreate, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        
        student_id = payload.get("sub")

        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM courses WHERE id = %s", (enrollment.course,))
        course = cursor.fetchone()

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        cursor.execute("select * from student_courses where student_id = %s and course_id = %s", (student_id, enrollment.course))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Student already enrolled in this course")
        
        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;", (student_id,))
        student = cursor.fetchone()

        if not student:
            raise HTTPException(status_code=404, detail="Student not found")  
          
        cursor.execute("INSERT INTO student_courses (student_id,student_name, course_id,course_name) VALUES (%s, %s, %s, %s)",
            (student_id, student.get("full_name"), enrollment.course, course.get("name"))
        )
 
        conn.commit()
        cursor.close()
        conn.close()
        return [EnrollmentOut(
            id=cursor.lastrowid,
            student_id=student_id,
            student_name=student.get("full_name"),
            course_id=enrollment.course,
            course_name=course.get("name"),
        )]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/enrollments/", response_model=List[EnrollmentOut], status_code=status.HTTP_200_OK, tags=["Courses"])
def get_all_enrollments(token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(user_id)
        if not permission.enrollments:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(" SELECT * from student_courses")
        enrollments = cursor.fetchall()

        cursor.close()
        conn.close()

        return enrollments

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/student/parent_contact/", response_model=List[ParentContactCreate], status_code=status.HTTP_200_OK, tags=["Students"])
def create_parent_contact(parent_data: ParentContactCreate, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_parent:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;", (student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        cursor.execute(
            "SELECT * FROM parents WHERE email = %s AND first_name = %s AND last_name = %s",
            (parent_data.email, parent_data.first_name, parent_data.last_name)
        )
        existing_parent = cursor.fetchone()
        if existing_parent:
            raise HTTPException(status_code=400, detail="Parent already exists")

        cursor.execute(
            "INSERT INTO parents (first_name, last_name, phone_number, email, relationship, address, full_name) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                parent_data.first_name,
                parent_data.last_name,
                parent_data.phone_number,
                parent_data.email,
                parent_data.relationship,
                parent_data.address,
                _generate_full_name(parent_data.first_name, parent_data.last_name)
            )
        )
        conn.commit()
        parent_id = cursor.lastrowid

        cursor.execute(
            " INSERT INTO student_parents (student_id, parent_id, student_name, parent_name) VALUES (%s, %s, %s, %s)",
                (student_id,parent_id,student.get("full_name"),_generate_full_name(parent_data.first_name, parent_data.last_name))
        )
        conn.commit()

        cursor.execute("SELECT first_name, last_name ,phone_number, email, relationship, address, full_name FROM parents WHERE id = %s", (parent_id,))
        new_parent = cursor.fetchone()

        cursor.close()
        conn.close()

        return [new_parent]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   
@app.post("/student/genrate_grades/", response_model=List[GradesOut], status_code=status.HTTP_201_CREATED, tags=["Grades"])
def create_grades(grades: grades, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_grades:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM courses WHERE id = %s", (grades.course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        cursor.execute("SELECT * FROM academic_terms WHERE id = %s", (grades.term_id,))
        term = cursor.fetchone()
        if not term:
          raise HTTPException(status_code=404, detail="Term not found")
        
        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;", (grades.student_id,))
        student = cursor.fetchone()
        if not student:
          raise HTTPException(status_code=404, detail="Student not found")
        
        cursor.execute("""INSERT INTO grades (student_id, student_name, course_id, course_name, term_id, term_name, grade, marks_obtained, total_marks, gpa) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                       (grades.student_id, student.get("full_name"), grades.course_id,course.get("name"),grades.term_id,term.get("name"),calculate_grade(grades.marks_obtained, grades.total_marks),grades.marks_obtained,grades.total_marks,round((grades.marks_obtained / grades.total_marks) * 4, 2)))
        
        conn.commit()

        cursor.execute("SELECT * FROM grades WHERE student_id = %s AND course_id = %s", (grades.student_id, grades.course_id))
        grades = cursor.fetchone()
        cursor.close()
        conn.close()

        return [grades]

    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/grades/", response_model=List[GradesOut], status_code=status.HTTP_200_OK, tags=["Grades"])
def get_student_grades(id:int,token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_grades:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;", (id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        cursor.execute("SELECT * FROM grades WHERE student_id = %s", (id,))
        grades = cursor.fetchall()
        if not grades:
            raise HTTPException(status_code=404, detail="Grades not found")
        cursor.close()
        conn.close()

        return grades

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/student/grades/delete/{id}", response_model=UpdateMessageResponse, status_code=status.HTTP_200_OK, tags=["Grades"])
def delete_grades(id: int, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_grades:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;", (id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        cursor.execute("SELECT * FROM grades WHERE student_id = %s", (id,))
        grade = cursor.fetchone()
        if not grade:
            raise HTTPException(status_code=404, detail="Grades not found")
        cursor.execute("DELETE FROM grades WHERE student_id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Grades deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/student/attendance/", response_model=List[AttendanceOut], status_code=status.HTTP_201_CREATED, tags=["Attendance"])
def create_attendance(attendance_data: AttendanceCreate, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )

        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_attendance:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        if attendance_data.status not in ['Present', 'Absent', 'Late', 'Excused']:
            raise HTTPException(status_code=400, detail="Invalid status")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;",
            (attendance_data.student_id,)
        )
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        cursor.execute(
            "SELECT * FROM attendance WHERE student_id = %s and date = %s",
            (attendance_data.student_id, attendance_data.date)
        )
        existing_attendance = cursor.fetchone()
        if existing_attendance:
            raise HTTPException(status_code=400, detail="Attendance already exists")

        cursor.execute(
            "INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)",
            (attendance_data.student_id, attendance_data.date, attendance_data.status)
        )
        new_id = cursor.lastrowid
        cursor.execute(
            "SELECT * FROM attendance WHERE id = %s",
            (new_id,)
        )
        new_attendance = cursor.fetchone()

        conn.commit()
        cursor.close()
        conn.close()

        return [new_attendance]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/student/attendance/{id}", response_model=AttendanceOut, tags=["Attendance"])
def get_attendance(
    id: int,
    token: str = Depends(oauth2_scheme)
):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_attendance:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;",
            (id,)
        )
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")


        cursor.execute(
          "SELECT * FROM attendance WHERE student_id = %s",
                (id,)
            )
        
        attendance_record = cursor.fetchone()
        if not attendance_record:
            raise HTTPException(status_code=404, detail="Attendance not found")

        cursor.close()
        conn.close()

        return attendance_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

UPLOAD_DIR = "uploads"  
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/student/documents/", status_code=status.HTTP_201_CREATED, tags=["Students"])
def upload_document(file: List[UploadFile] = File(...),token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;",
            (student_id,)
        )
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        uploaded_files = []
        for f in file:
            file_location = os.path.join(UPLOAD_DIR, f.filename)

            with open(file_location, "wb") as file_object:
                file_object.write(f.file.read())

            cursor.execute("""
                INSERT INTO student_documents (student_id, file_name, file_path)
                VALUES (%s, %s, %s)
            """, (student_id, f.filename, file_location))

            uploaded_files.append(f.filename)

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Files uploaded successfully", "files": uploaded_files}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/documents/download_all/{student_id}", tags=["Students"])
async def download_all_documents(student_id: int, background_tasks: BackgroundTasks, token: str = Depends(oauth2_scheme)):
    token_str = token.credentials
    payload = decode_token(token_str)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if token.credentials != token_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token provided")

    token_student_id = payload.get("sub")
    if not token_student_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    permission = _get_user_permissions(token_student_id)
    if not permission.student_document:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student_documents WHERE student_id = %s", (student_id,))
    documents = cursor.fetchall()
    cursor.close()
    conn.close()

    if not documents:
        raise HTTPException(status_code=404, detail="No documents found")

    file_paths = []
    for doc in documents:
        if os.path.exists(doc["file_path"]):
            file_paths.append(doc["file_path"])

    if not file_paths:
        raise HTTPException(status_code=404, detail="No files found on server")

    zip_filename = f"student_{student_id}_documents.zip"
    temp_zip_path = os.path.join(UPLOAD_DIR, zip_filename)

    try:
       with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
         for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))

       background_tasks.add_task(os.remove, temp_zip_path)

       return FileResponse(
           path=temp_zip_path,
           media_type="application/zip",
           filename=zip_filename,
           headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
       )
    except Exception as e:
       if os.path.exists(temp_zip_path):
           os.remove(temp_zip_path)
       raise HTTPException(status_code=500, detail=f"Error creating zip file: {e}")

@app.post("/student/fees-category/", response_model=List[FeesCategory], status_code=status.HTTP_201_CREATED, tags=["Fees"])
def create_fees_category(fees_category: FeesCategory,token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_fees:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM fee_categories WHERE name = %s", (fees_category.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Fees category already exists")
        
        cursor.execute(
            "INSERT INTO fee_categories (name, amount, description) VALUES (%s, %s, %s)",
            (fees_category.name, fees_category.amount, fees_category.description)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return [fees_category]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/student/{id}/fees/", response_model=List[StudentFee], status_code=status.HTTP_201_CREATED, tags=["Fees"])
def create_student_fee(student_fee: StudentFee,token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.create_fees:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM fee_categories WHERE id = %s", (student_fee.fee_category_id,))
        fee_category = cursor.fetchone()
        if not fee_category:
            raise HTTPException(status_code=404, detail="Fee category not found")
        
        cursor.execute("SELECT * FROM students WHERE user_id = %s;", (student_fee.student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        total_amount = Decimal(fee_category.get("amount", 0))

        cursor.execute("INSERT INTO student_fees (student_id, fee_category_id, due_amount, due_date,total_amount) VALUES (%s, %s, %s, %s, %s)",
            (student_fee.student_id, student_fee.fee_category_id, student_fee.due_amount, student_fee.due_date, total_amount)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return [student_fee]
    except Exception as e:    
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/student/fees/{id}", response_model=List[StudentFeeUpdate], status_code=status.HTTP_200_OK, tags=["Fees"])
def get_student_fee_details(id: int,token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.student_fees:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM student_fees WHERE student_id = %s", (id,))
        fee = cursor.fetchall()
        if not fee:
            raise HTTPException(status_code=404, detail="Fees not found")
        cursor.close()
        conn.close()
        return fee
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post(
    "/student/fee-payment/{id}",
    response_model=List[PaymentOut],
    status_code=status.HTTP_201_CREATED,
    tags=["Fees"]
)
async def create_student_fee_payment(id: int,payment: payments, token: str = Depends(oauth2_scheme)):
    try:
      
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(status_code=401, detail="Invalid token provided")

        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM students WHERE user_id = %s;", (id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        cursor.execute("SELECT * FROM student_fees WHERE student_id = %s", (id,))
        student_fee = cursor.fetchone()
        if not student_fee:
            raise HTTPException(status_code=404, detail="Fee record not found")

        cursor.execute("SELECT * FROM fee_categories WHERE id = %s;", (payment.fee_category_id,))
        fee_category = cursor.fetchone()
        if not fee_category:
            raise HTTPException(status_code=404, detail="Fee category not found")
        
        cursor.execute("SELECT status FROM student_fees WHERE student_id = %s", (id,))
        status_row = cursor.fetchone()
        
        if status_row and status_row["status"].lower() == "paid":
            raise HTTPException(status_code=400, detail="Fees already paid")

        if payment.amount_paid <= 0:
            raise HTTPException(status_code=400, detail="Amount paid must be greater than zero")

        cursor.execute("""
            INSERT INTO payments (student_fee_id, amount_paid, payment_method, fee_category_name)
            VALUES (%s, %s, %s, %s)
        """, (
            student_fee["student_id"],  
            payment.amount_paid,
            payment.payment_method,
            fee_category["name"]
        ))
        conn.commit()

        cursor.execute("""
            SELECT * FROM payments
            WHERE student_fee_id = %s
            ORDER BY created_at DESC
        """, (student_fee["student_id"],))
        payments_list = cursor.fetchall()

        cursor.execute("update student_fees set status = 'paid' where id = %s", (student_fee["id"],))
        conn.commit()
        cursor.close()
        conn.close()
        
        return payments_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/fees/{id}/details", response_model=List[paymentsdetails], status_code=status.HTTP_200_OK, tags=["Fees"])
def get_student_fee_details(id: int, token: str = Depends(oauth2_scheme)):
    try:
        token_str = token.credentials
        payload = decode_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if token.credentials != token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token provided"
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        permission = _get_user_permissions(student_id)
        if not permission.student_fees:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'student' AND is_active = 1;", (id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        cursor.execute("SELECT * FROM student_fees WHERE student_id = %s AND status = 'paid'", (id,))
        student_fee = cursor.fetchone()
        if not student_fee:
            raise HTTPException(status_code=404, detail="Fee record not found or Not paid")
        
        cursor.execute("""
            SELECT p.id, p.amount_paid,
             p.payment_method, p.payment_date,
             p.receipt_number, u.full_name, sf.status
            FROM payments p INNER JOIN student_fees sf ON p.student_fee_id = sf.student_id
            INNER JOIN students s ON sf.student_id = s.user_id 
            INNER JOIN users u ON s.user_id = u.id WHERE u.id = %s
        """, (student_fee["student_id"],))
        
        payments_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return payments_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)  