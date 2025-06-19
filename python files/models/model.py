import asyncio
import logging
import torch
from typing import List, Dict
import sys
import os
from huggingface_hub import login
from peft import PeftModel


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ..data_models.data_models import PatientInput, Prescription

# Only import transformers if available
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available, using mock model")

logger = logging.getLogger(__name__)

class BioGPTModelManager:
    """BioGPT model manager for prescription generation"""
    
    def __init__(self, model_name: str = "santanukumar07/biogpt-finetune", use_mock: bool = False, hf_token: str = ""):
        self.model_name = model_name
        self.current_version = "1.0"
        self.tokenizer = None
        self.model = None
        self.hf_token = hf_token
        self.use_mock = use_mock or not TRANSFORMERS_AVAILABLE
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"BioGPT Manager initialized - Mock mode: {self.use_mock}")
        logger.info(f"Using device: {self.device}")
    
    async def load_model(self):
        """Load BioGPT model and tokenizer"""
        if self.use_mock:
            logger.info("Using mock model for demonstration")
            return
            
        try:
            # Authenticate with Hugging Face if token provided
            if self.hf_token:
                logger.info("Authenticating with Hugging Face...")
                login(token=self.hf_token)
            elif os.getenv('HUGGINGFACE_TOKEN'):
                logger.info("Using HF token from environment...")
                login(token=os.getenv('HUGGINGFACE_TOKEN'))
            
            logger.info(f"Loading BioGPT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_auth_token=True if self.hf_token or os.getenv('HUGGINGFACE_TOKEN') else None
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                    "microsoft/biogpt",
                    use_auth_token=True if self.hf_token or os.getenv('HUGGINGFACE_TOKEN') else None
                )
            self.model = PeftModel.from_pretrained(
                        base_model,
                        self.model_name,
                        use_auth_token=True if self.hf_token or os.getenv('HUGGINGFACE_TOKEN') else None
                    )
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            logger.info("BioGPT model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Falling back to mock model")
            self.use_mock = True
    
    def format_input(self, patient_input: PatientInput) -> str:
        """Format patient input for BioGPT"""
        return (f"symptoms:{patient_input.symptoms}, "
                f"age:{patient_input.age}, "
                f"gender:{patient_input.gender}, "
                f"diagnosis:{patient_input.diagnosis}")
    
    async def generate_prescription(self, patient_input: PatientInput) -> Prescription:
        """Generate prescription using BioGPT model"""
        try:
            if self.use_mock:
                medications = await self._mock_generate_prescription(patient_input)
                confidence = self._calculate_mock_confidence(patient_input)
            else:
                medications, confidence = await self._real_generate_prescription(patient_input)
            
            return Prescription(
                medications=medications,
                confidence=confidence,
                model_version=self.current_version
            )
            
        except Exception as e:
            logger.error(f"Error generating prescription: {e}")
            return Prescription(
                medications=["Error: Unable to generate prescription"],
                confidence=0.0,
                model_version=self.current_version
            )
    
    async def _real_generate_prescription(self, patient_input: PatientInput) -> tuple:
        """Real BioGPT inference"""
        try:
            input_text = self.format_input(patient_input)
            logger.info(f"Generating prescription for: {input_text}")
            
            inputs = self.tokenizer(input_text, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=inputs.input_ids.shape[1] + 50,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            medications = self._extract_medications(generated_text)
            confidence = self._calculate_confidence(outputs, inputs)
            
            logger.info(f"Generated medications: {medications}")
            return medications, confidence
            
        except Exception as e:
            logger.error(f"Error in real prescription generation: {e}")
            # Fallback to mock
            medications = await self._mock_generate_prescription(patient_input)
            confidence = 0.5
            return medications, confidence
    
    async def _mock_generate_prescription(self, patient_input: PatientInput) -> List[str]:
        """Mock prescription generation for demonstration"""
        # Add small delay to simulate processing
        await asyncio.sleep(0.5)
        
        medications = []
        symptoms = patient_input.symptoms.lower()
        diagnosis = patient_input.diagnosis.lower()
        age = patient_input.age
        
        # Symptom-based medications
        symptom_mapping = {
            'back pain': ['Ibuprofen', 'Acetaminophen'],
            'pain': ['Acetaminophen', 'Ibuprofen'],
            'constipation': ['Docusate Sodium', 'Senna'],
            'loss of appetite': ['Multivitamin', 'B-Complex'],
            'fatigue': ['Iron Supplement', 'Vitamin B12'],
            'headache': ['Acetaminophen', 'Ibuprofen'],
            'nausea': ['Ondansetron', 'Ginger Extract'],
            'dizziness': ['Meclizine'],
            'chest pain': ['Nitroglycerin'],
            'shortness of breath': ['Albuterol'],
            'cough': ['Dextromethorphan', 'Guaifenesin']
        }
        
        for symptom, meds in symptom_mapping.items():
            if symptom in symptoms:
                medications.extend(meds)
        
        # Diagnosis-based medications
        diagnosis_mapping = {
            'hypertension': ['Lisinopril', 'Amlodipine'],
            'diabetes': ['Metformin', 'Glipizide'],
            'depression': ['Sertraline', 'Fluoxetine'],
            'anxiety': ['Lorazepam', 'Alprazolam'],
            'arthritis': ['Celecoxib', 'Naproxen'],
            'asthma': ['Albuterol', 'Fluticasone'],
            'heart disease': ['Aspirin', 'Metoprolol']
        }
        
        for condition, meds in diagnosis_mapping.items():
            if condition in diagnosis:
                medications.extend(meds)
        
        # Age-based considerations
        if age > 65:
            medications.extend(['Vitamin D', 'Calcium'])
        elif age < 18:
            # Remove medications not suitable for children
            medications = [med for med in medications if 'Aspirin' not in med]
        
        # Remove duplicates and ensure we have at least one medication
        medications = list(set(medications))
        if not medications:
            medications = ['General Supportive Care', 'Multivitamin']
        
        logger.info(f"Mock generated medications: {medications}")
        return medications
    
    def _calculate_mock_confidence(self, patient_input: PatientInput) -> float:
        """Calculate mock confidence score"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on available information
        if patient_input.symptoms:
            confidence += 0.2
        if patient_input.diagnosis:
            confidence += 0.2
        if patient_input.age > 0:
            confidence += 0.1
        
        # Decrease confidence for complex cases
        symptom_count = len(patient_input.symptoms.split(','))
        if symptom_count > 3:
            confidence -= 0.1
        
        return min(max(confidence, 0.1), 0.95)  # Keep between 0.1 and 0.95
    
    def _extract_medications(self, generated_text: str) -> List[str]:
        """Extract medication names from generated text"""
        # This is a simplified extraction - in real implementation,
        # you would use NER or more sophisticated parsing
        
        medications = []
        lines = generated_text.split('\n')
        
        # Common medication keywords
        medication_keywords = [
            'prescribe', 'medication', 'drug', 'treatment', 'therapy'
        ]
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in medication_keywords):
                # Extract potential medication names (capitalized words)
                words = line.split()
                for word in words:
                    if (word.istitle() and len(word) > 3 and 
                        not word.lower() in ['the', 'and', 'for', 'with', 'patient']):
                        medications.append(word)
        
        # Fallback: look for common medication patterns
        if not medications:
            # Simple pattern matching for common medications
            common_meds = [
                'Aspirin', 'Ibuprofen', 'Acetaminophen', 'Lisinopril', 
                'Metformin', 'Amlodipine', 'Simvastatin'
            ]
            for med in common_meds:
                if med.lower() in generated_text.lower():
                    medications.append(med)
        
        return medications if medications else ['Generated Medication']
    
    def _calculate_confidence(self, outputs, inputs) -> float:
        """Calculate confidence score from model outputs"""
        try:
            # Simple confidence calculation based on output probabilities
            # In real implementation, this would be more sophisticated
            return 0.85  # Placeholder
        except:
            return 0.5
    
    async def update_model_with_feedback(self, feedback_data: List[Dict]) -> str:
        """Update/fine-tune model with doctor feedback"""
        logger.info(f"Starting model update with {len(feedback_data)} feedback samples")
        
        if self.use_mock:
            return await self._mock_update_model(feedback_data)
        else:
            return await self._real_update_model(feedback_data)
    
    async def _mock_update_model(self, feedback_data: List[Dict]) -> str:
        """Mock model update for demonstration"""
        # Simulate training time
        await asyncio.sleep(2)
        
        old_version = self.current_version
        version_parts = self.current_version.split('.')
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        self.current_version = '.'.join(version_parts)
        
        logger.info(f"Mock model updated from {old_version} to {self.current_version}")
        logger.info(f"Processed {len(feedback_data)} feedback samples")
        
        return self.current_version
    
    async def _real_update_model(self, feedback_data: List[Dict]) -> str:
        """Real model fine-tuning with feedback data"""
        try:
            # In a real implementation, this would:
            # 1. Prepare training data from feedback
            # 2. Create data loaders
            # 3. Fine-tune the model
            # 4. Save the updated model
            
            logger.info("Real model update not implemented in this demo")
            logger.info("Would fine-tune BioGPT with feedback data")
            
            # For now, just update version
            old_version = self.current_version
            version_parts = self.current_version.split('.')
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            self.current_version = '.'.join(version_parts)
            
            logger.info(f"Model version updated from {old_version} to {self.current_version}")
            return self.current_version
            
        except Exception as e:
            logger.error(f"Error in real model update: {e}")
            return await self._mock_update_model(feedback_data)
    
    def get_model_info(self) -> Dict:
        """Get current model information"""
        return {
            'model_name': self.model_name,
            'version': self.current_version,
            'device': str(self.device),
            'mock_mode': self.use_mock,
            'loaded': self.model is not None or self.use_mock
        }

# Test the model manager
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_model():
        # Test with mock model
        model_manager = BioGPTModelManager(
                model_name="santanukumar07/biogpt-finetune",
                hf_token=""  # ADD YOUR TOKEN HERE
            )
        await model_manager.load_model()
        
        # Test prescription generation
        patient = PatientInput(
            symptoms="back pain, loss of appetite, constipation",
            age=74,
            gender="male",
            diagnosis="hypertension diabetes"
        )
        
        prescription = await model_manager.generate_prescription(patient)
        print(f"Generated prescription: {prescription.to_dict()}")
        
        # Test model update
        mock_feedback = [
            {
                'symptoms': 'back pain',
                'original_prescription': ['Ibuprofen'],
                'modified_prescription': ['Ibuprofen', 'Vitamin D'],
                'feedback_notes': 'Added vitamin D'
            }
        ]
        
        new_version = await model_manager.update_model_with_feedback(mock_feedback)
        print(f"Model updated to version: {new_version}")
        
        # Get model info
        info = model_manager.get_model_info()
        print(f"Model info: {info}")
    
    asyncio.run(test_model())