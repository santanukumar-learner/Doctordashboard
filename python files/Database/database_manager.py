import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..data_models.data_models import PatientInput, Prescription, DoctorFeedback

import sqlite3
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)





class MedicalDatabase:
    """Database manager for medical MCP system"""
    
    def __init__(self, db_path: str = "medical_mcp.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Patient inputs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patient_inputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symptoms TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    diagnosis TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Prescriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prescriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_input_id INTEGER,
                    medications TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    model_version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (patient_input_id) REFERENCES patient_inputs (id)
                )
            ''')
            
            # Doctor feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctor_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prescription_id INTEGER,
                    original_prescription TEXT NOT NULL,
                    modified_prescription TEXT NOT NULL,
                    feedback_notes TEXT,
                    doctor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (prescription_id) REFERENCES prescriptions (id)
                )
            ''')
            
            # Model versions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    training_data_count INTEGER,
                    feedback_incorporated INTEGER,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def save_patient_input(self, patient_input: PatientInput) -> int:
        """Save patient input and return patient ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patient_inputs (symptoms, age, gender, diagnosis, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (patient_input.symptoms, patient_input.age, patient_input.gender, 
                  patient_input.diagnosis, patient_input.timestamp))
            patient_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Patient input saved with ID: {patient_id}")
            return patient_id
        except Exception as e:
            logger.error(f"Error saving patient input: {e}")
            raise

    def save_prescription(self, prescription: Prescription, patient_input_id: int) -> int:
        """Save prescription and return prescription ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prescriptions (patient_input_id, medications, confidence, model_version, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (patient_input_id, json.dumps(prescription.medications), 
                  prescription.confidence, prescription.model_version, prescription.timestamp))
            prescription_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Prescription saved with ID: {prescription_id}")
            return prescription_id
        except Exception as e:
            logger.error(f"Error saving prescription: {e}")
            raise

    def save_doctor_feedback(self, feedback: DoctorFeedback, prescription_id: int) -> int:
        """Save doctor feedback and return feedback ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO doctor_feedback (prescription_id, original_prescription, 
                                           modified_prescription, feedback_notes, doctor_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (prescription_id, json.dumps(feedback.original_prescription),
                  json.dumps(feedback.modified_prescription), feedback.feedback_notes,
                  feedback.doctor_id, feedback.timestamp))
            feedback_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Doctor feedback saved with ID: {feedback_id}")
            return feedback_id
        except Exception as e:
            logger.error(f"Error saving doctor feedback: {e}")
            raise

    def get_patient_input(self, patient_id: int) -> Optional[PatientInput]:
        """Get patient input by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM patient_inputs WHERE id = ?', (patient_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return PatientInput(
                    symptoms=row[1],
                    age=row[2],
                    gender=row[3],
                    diagnosis=row[4],
                    timestamp=row[5]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting patient input: {e}")
            return None

    def get_prescription(self, prescription_id: int) -> Optional[Prescription]:
        """Get prescription by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM prescriptions WHERE id = ?', (prescription_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Prescription(
                    medications=json.loads(row[2]),
                    confidence=row[3],
                    model_version=row[4],
                    patient_id=str(row[1]),
                    timestamp=row[5]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting prescription: {e}")
            return None

    def get_feedback_for_training(self, limit: int = 100) -> List[Dict]:
        """Get feedback data for model training"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pi.symptoms, pi.age, pi.gender, pi.diagnosis,
                       df.original_prescription, df.modified_prescription, df.feedback_notes
                FROM doctor_feedback df
                JOIN prescriptions p ON df.prescription_id = p.id
                JOIN patient_inputs pi ON p.patient_input_id = pi.id
                ORDER BY df.timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            
            logger.info(f"Retrieved {len(results)} feedback records for training")
            return results
        except Exception as e:
            logger.error(f"Error getting feedback for training: {e}")
            return []

    def get_model_stats(self) -> Dict:
        """Get model statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count total patients
            cursor.execute('SELECT COUNT(*) FROM patient_inputs')
            total_patients = cursor.fetchone()[0]
            
            # Count total prescriptions
            cursor.execute('SELECT COUNT(*) FROM prescriptions')
            total_prescriptions = cursor.fetchone()[0]
            
            # Count total feedback
            cursor.execute('SELECT COUNT(*) FROM doctor_feedback')
            total_feedback = cursor.fetchone()[0]
            
            # Get latest model version
            cursor.execute('SELECT version FROM model_versions ORDER BY created_at DESC LIMIT 1')
            latest_version = cursor.fetchone()
            latest_version = latest_version[0] if latest_version else "1.0"
            
            conn.close()
            
            return {
                'total_patients': total_patients,
                'total_prescriptions': total_prescriptions,
                'total_feedback': total_feedback,
                'latest_model_version': latest_version
            }
        except Exception as e:
            logger.error(f"Error getting model stats: {e}")
            return {}

    def save_model_version(self, version: str, training_data_count: int, feedback_count: int):
        """Save new model version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO model_versions (version, training_data_count, feedback_incorporated, created_at)
                VALUES (?, ?, ?, ?)
            ''', (version, training_data_count, feedback_count, 
                  datetime.now().isoformat()))
            conn.commit()
            conn.close()
            logger.info(f"Model version {version} saved")
        except Exception as e:
            logger.error(f"Error saving model version: {e}")
            raise

    def close(self):
        """Close database connection"""
        # SQLite connections are closed automatically in our implementation
        pass

# Test the database
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test database operations
    db = MedicalDatabase("test_medical.db")
    
    # Test patient input
    patient = PatientInput(
        symptoms="back pain, fatigue",
        age=45,
        gender="female",
        diagnosis="hypertension"
    )
    
    patient_id = db.save_patient_input(patient)
    print(f"Saved patient with ID: {patient_id}")
    
    # Test prescription
    prescription = Prescription(
        medications=["Ibuprofen", "Lisinopril"],
        confidence=0.85,
        model_version="1.0"
    )
    
    prescription_id = db.save_prescription(prescription, patient_id)
    print(f"Saved prescription with ID: {prescription_id}")
    
    # Test doctor feedback
    feedback = DoctorFeedback(
        original_prescription=["Ibuprofen", "Lisinopril"],
        modified_prescription=["Ibuprofen", "Lisinopril", "Vitamin D"],
        feedback_notes="Added vitamin D for bone health",
        doctor_id="dr_test",
        patient_input=patient
    )
    
    feedback_id = db.save_doctor_feedback(feedback, prescription_id)
    print(f"Saved feedback with ID: {feedback_id}")
    
    # Test stats
    stats = db.get_model_stats()
    print(f"Database stats: {stats}")