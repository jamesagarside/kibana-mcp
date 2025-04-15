from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
import uuid
import re

# Entry models for different entry types
class BaseEntry(BaseModel):
    field: str
    operator: Literal["included", "excluded"] = "included"
    type: str

class ExistsEntry(BaseEntry):
    type: Literal["exists"] = "exists"

class MatchAnyEntry(BaseEntry):
    type: Literal["match_any"] = "match_any"
    value: List[str]

class MatchEntry(BaseEntry):
    type: Literal["match"] = "match"
    value: str

# Union type for all possible entry types
EntryType = Union[ExistsEntry, MatchAnyEntry, MatchEntry]

class ExceptionItem(BaseModel):
    """Model for a single exception item to be added to a rule's exception list."""
    name: str
    type: Literal["simple"] = "simple"
    entries: List[EntryType]
    description: str
    
    # Optional fields
    tags: Optional[List[str]] = None
    item_id: Optional[str] = None
    list_id: Optional[str] = None
    os_types: Optional[List[Literal["windows", "linux", "macos"]]] = None
    namespace_type: Optional[Literal["single", "agnostic"]] = "single"

class AddRuleExceptionItemsRequest(BaseModel):
    """Model for the request to add exception items to a rule."""
    rule_id: str
    items: List[ExceptionItem]
    
    # UUID validation for rule_id
    @field_validator('rule_id')
    @classmethod
    def validate_uuid(cls, v):
        """Validate that rule_id is a valid UUID."""
        # UUID pattern regex
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        # Check if it's a valid UUID format
        if not uuid_pattern.match(v):
            try:
                # Try to parse it as a UUID to catch any edge cases
                uuid.UUID(v)
            except ValueError:
                raise ValueError(f"Invalid UUID format for rule_id: {v}")
        
        return v
