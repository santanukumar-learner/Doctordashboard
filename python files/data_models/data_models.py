from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class PatientInput:
    """Patient input data structure"""
    symptoms: str
    age: int
    gender: str
    diagnosis: str
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Prescription:
    """Prescription data structure"""
    medications: List[str]
    confidence: float
    model_version: str
    patient_id: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)

@dataclass
class DoctorFeedback:
    """Doctor feedback data structure"""
    original_prescription: List[str]
    modified_prescription: List[str]
    feedback_notes: str
    doctor_id: str
    patient_input: PatientInput
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)

@dataclass
class MCPMessage:
    """MCP message structure"""
    message_type: str
    data: dict
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)

@dataclass
class MCPResponse:
    """MCP response structure"""
    message_type: str
    status: str
    data: dict = None
    error_message: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)