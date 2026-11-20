from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class StudentSummary(BaseModel):
    student_id: int
    presentation: str
    risk_score: float
    flagged: bool

class StudentRiskCard(BaseModel):
    student_id: int
    presentation: str
    window: str
    risk_score: float
    threshold_applied: float
    flagged: bool
    top_positive_factors: list[dict]
    top_negative_factors: list[dict]
    other_factors_sum: float
    base_value: float

class SCSQuestion(BaseModel):
    id: int
    text: str

class SCSResponseItem(BaseModel):
    id: int
    score: int

class SCSSubmission(BaseModel):
    responses: list[SCSResponseItem]

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    active: bool

class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # "admin" | "advisor"

class UserUpdate(BaseModel):
    role: str | None = None
    active: bool | None = None
    password: str | None = None

class RiskBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int

class TopFeature(BaseModel):
    feature: str
    mean_abs_shap: float

class WindowStats(BaseModel):
    window: str
    n_students: int
    n_flagged: int
    flagged_pct: float
    risk_bins: list[RiskBin]
    top_features: list[TopFeature]

class StudentPage(BaseModel):
    items: list[StudentSummary]
    total: int
    limit: int
    offset: int

