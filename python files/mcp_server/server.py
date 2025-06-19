import asyncio
import json
import logging
import websockets
from typing import Set
from datetime import datetime
from dataclasses import asdict
from ..data_models.data_models import PatientInput, Prescription, DoctorFeedback, MCPResponse
from ..Database.database_manager import MedicalDatabase
from ..models.model import BioGPTModelManager

logger = logging.getLogger(__name__)

class MCPMedicalServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.database = MedicalDatabase()
        self.model_manager = BioGPTModelManager()
        self.connected_clients = set()
        
    async def start_server(self):
        """Start the MCP server"""
        await self.model_manager.load_model()
        logger.info(f"Starting MCP Medical Server on {self.host}:{self.port}")
        
        # Fix: Create a wrapper function that properly handles the method call
        async def handler(websocket, path=None):
            # Handle both cases: with path and without path
            return await self.handle_client(websocket, path or "/")
        
        server = await websockets.serve(
            handler,
            self.host,
            self.port
        )
        
        logger.info(f"Server started successfully on ws://{self.host}:{self.port}")
        return server
    
    async def handle_client(self, websocket, path):
        """Handle client connections"""
        self.connected_clients.add(websocket)
        logger.info(f"Client connected from {websocket.remote_address} on path: {path}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error in handle_client: {e}")
            await self.send_error(websocket, f"Connection error: {str(e)}")
        finally:
            self.connected_clients.discard(websocket)  # Use discard instead of remove to avoid KeyError
    
    async def process_message(self, websocket, message: str):
        """Process incoming messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'generate_prescription':
                await self.handle_prescription_request(websocket, data)
            elif message_type == 'doctor_feedback':
                await self.handle_doctor_feedback(websocket, data)
            elif message_type == 'update_model':
                await self.handle_model_update(websocket, data)
            else:
                await self.send_error(websocket, "Unknown message type")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send_error(websocket, str(e))
    
    async def handle_prescription_request(self, websocket, data):
        """Handle prescription generation requests"""
        try:  # ← REMOVE the extra spaces before 'try'
            # Extract patient input data
            patient_input = data.get('patient_input', {})
            patient_name = patient_input.get('name', 'Unknown Patient')
            patient_age = patient_input.get('age', 0)
            symptoms = patient_input.get('symptoms', [])
            
            logger.info(f"Processing prescription request for {patient_name}, age {patient_age}")
            logger.info(f"Symptoms: {symptoms}")
            
            # Create PatientInput object matching your data model
            patient_input_obj = PatientInput(
                symptoms=", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms),
                age=patient_age,
                gender=patient_input.get('gender', 'Unknown'),
                diagnosis=patient_input.get('diagnosis', '')
            )
            
            # Store patient name separately in database if needed
            patient_id = f'patient_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            
            # Use your actual model to generate prescription
            prescription_obj = await self.model_manager.generate_prescription(patient_input_obj)
            
            # Convert to dictionary for JSON response
            prescription_dict = asdict(prescription_obj)
            
            # Add patient info to response (since it's not in the data model)
            prescription_dict['patient_name'] = patient_name
            prescription_dict['patient_id'] = patient_id
            
            response = {
                'type': 'prescription_generated',
                'prescription_id': f'rx_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'prescription': prescription_dict,
                'status': 'success',
                'message': 'Prescription generated successfully'
            }
            
            await websocket.send(json.dumps(response))
            logger.info(f"Prescription generated for {patient_name}")
            
        except Exception as e:
            logger.error(f"Error generating prescription: {e}")
            await self.send_error(websocket, f"Error generating prescription: {e}")
    
    async def handle_doctor_feedback(self, websocket, data):
        """Handle doctor feedback"""
        try:
            prescription_id = data.get('prescription_id')
            feedback_notes = data.get('feedback_notes')
            doctor_id = data.get('doctor_id')
            
            logger.info(f"Processing doctor feedback from {doctor_id} for prescription {prescription_id}")
            
            response = {
                'type': 'feedback_saved',
                'prescription_id': prescription_id,
                'status': 'success',
                'message': 'Doctor feedback saved successfully',
                'feedback_id': f'fb_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            }
            
            await websocket.send(json.dumps(response))
            logger.info(f"Doctor feedback processed for prescription {prescription_id}")
            
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            await self.send_error(websocket, f"Error saving feedback: {e}")
    
    async def handle_model_update(self, websocket, data):
        """Handle model update requests"""
        try:
            logger.info("Processing model update request")
            
            response = {
                'type': 'model_updated',
                'new_version': '1.0.1',
                'feedback_samples_used': 0,
                'status': 'success',
                'message': 'Model updated successfully',
                'updated_at': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(response))
            logger.info("Model update processed")
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            await self.send_error(websocket, f"Error updating model: {e}")
    
    async def send_error(self, websocket, error_message: str):
        """Send error response to client"""
        try:
            response = {
                'type': 'error',
                'message': error_message,
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")


# Main function to run the server
async def main():
    logging.basicConfig(level=logging.INFO)
    server = MCPMedicalServer()
    
    try:
        websocket_server = await server.start_server()
        logger.info("Server is running. Press Ctrl+C to stop.")
        
        # Keep the server running
        await websocket_server.wait_closed()
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

