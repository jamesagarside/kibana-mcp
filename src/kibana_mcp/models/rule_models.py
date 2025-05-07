from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class SortField(str, Enum):
    """Valid sort fields for the find_rules API."""
    CREATED_AT = "created_at"
    CREATED_AT_CAMEL = "createdAt"
    ENABLED = "enabled"
    LAST_EXECUTION_DATE = "execution_summary.last_execution.date"
    EXECUTION_GAP = "execution_summary.last_execution.metrics.execution_gap_duration_s"
    TOTAL_INDEXING_DURATION = "execution_summary.last_execution.metrics.total_indexing_duration_ms"
    TOTAL_SEARCH_DURATION = "execution_summary.last_execution.metrics.total_search_duration_ms"
    EXECUTION_STATUS = "execution_summary.last_execution.status"
    NAME = "name"
    RISK_SCORE = "risk_score"
    RISK_SCORE_CAMEL = "riskScore"
    SEVERITY = "severity"
    UPDATED_AT = "updated_at"
    UPDATED_AT_CAMEL = "updatedAt"

class SortOrder(str, Enum):
    """Valid sort orders for the find_rules API."""
    ASC = "asc"
    DESC = "desc"

class FindRulesRequest(BaseModel):
    """Model for the request to find detection rules."""
    # For filter, field names must be prefixed with 'alert.attributes.'
    # Example: 'alert.attributes.name:"Rule Name"' to filter by name
    filter: Optional[str] = None
    sort_field: Optional[SortField] = None
    sort_order: Optional[SortOrder] = None
    page: Optional[int] = Field(None, ge=1)
    per_page: Optional[int] = Field(None, ge=0)
