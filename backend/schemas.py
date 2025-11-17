from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class SubmitIn(BaseModel):
    url: HttpUrl
    user_id: Optional[int] = None

class SubmitOut(BaseModel):
    job_id: str
    status: str

class CheckResult(BaseModel):
    name: str
    ok: bool
    reason: str
    details: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    url: str
    job_id: str
    checks: List[CheckResult]
    score: int
    level: str  # baixo, médio, alto
    tips: List[str]

class SubmissionStatus(BaseModel):
    id: int
    url: str
    status: str
    result: Optional[AnalysisResult] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

class TrainingCaseOut(BaseModel):
    id: int
    title: str
    description: str
    payload_url: str
    lesson: Dict[str, Any]
    created_at: datetime

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

