import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
    
    async def connect(self):
        """Connect to the MCP server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Connected to server at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")
    
    async def generate_prescription(self, patient_data: dict, symptoms: list):
        """Generate a prescription"""
        if not self.websocket:
            raise Exception("Not connected to server")
        
        message = {
            "type": "generate_prescription",
            "patient_input": {
                "name": patient_data.get("name", "Unknown"),  # Keep name for display
                "age": patient_data.get("age", 0),
                "gender": patient_data.get("gender", "Unknown"),  # Add gender
                "symptoms": symptoms,
                "diagnosis": patient_data.get("diagnosis", ""),  # Add diagnosis
                "medical_history": patient_data.get("medical_history", []),
                "allergies": patient_data.get("allergies", [])
            }
        }
        
        try:
            # Send request
            await self.websocket.send(json.dumps(message))
            logger.info("Prescription request sent")
            
            # Wait for response
            response = await self.websocket.recv()
            result = json.loads(response)
            
            if result.get("status") == "success":
                logger.info("Prescription generated successfully")
                return result
            else:
                logger.error(f"Error from server: {result.get('message', 'Unknown error')}")
                return result
                
        except websockets.exceptions.ConnectionClosed:
            logger.error("Connection closed while waiting for response")
            raise Exception("Connection closed")
        except Exception as e:
            logger.error(f"Error generating prescription: {e}")
            raise
    
    async def send_doctor_feedback(self, prescription_id: str, feedback_data: dict):
        """Send doctor feedback"""
        if not self.websocket:
            raise Exception("Not connected to server")
        
        message = {
            "type": "doctor_feedback",
            "prescription_id": prescription_id,
            "original_prescription": feedback_data.get("original_prescription"),
            "modified_prescription": feedback_data.get("modified_prescription"),
            "feedback_notes": feedback_data.get("feedback_notes"),
            "doctor_id": feedback_data.get("doctor_id"),
            "patient_input": feedback_data.get("patient_input")
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.info("Doctor feedback sent")
            
            response = await self.websocket.recv()
            result = json.loads(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending feedback: {e}")
            raise
    
    async def update_model(self):
        """Request model update"""
        if not self.websocket:
            raise Exception("Not connected to server")
        
        message = {
            "type": "update_model"
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.info("Model update request sent")
            
            response = await self.websocket.recv()
            result = json.loads(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            raise

async def main():
    """Test the client"""
    client = MCPClient()
    
    try:
        # Connect to server
        if not await client.connect():
            logger.error("Failed to connect to server")
            return
        
        # Test prescription generation
        patient_data = {
            "name": "John Doe",
            "age": 35,
            "medical_history": ["hypertension"],
            "allergies": ["penicillin"]
        }
        
        symptoms = ["fever", "headache", "body ache"]
        
        logger.info("Testing prescription generation...")
        result = await client.generate_prescription(patient_data, symptoms)
        
        if result.get("status") == "success":
            print("\n=== PRESCRIPTION GENERATED ===")
            print(f"Prescription ID: {result.get('prescription_id')}")
            print(f"Prescription: {json.dumps(result.get('prescription'), indent=2)}")
        else:
            print(f"\nError: {result.get('message')}")
        
        # Test doctor feedback
        logger.info("Testing doctor feedback...")
        feedback_data = {
            "original_prescription": result.get('prescription', {}),
            "modified_prescription": {"modified": True},
            "feedback_notes": "Good prescription, minor adjustments made",
            "doctor_id": "DR001",
            "patient_input": patient_data
        }
        
        feedback_result = await client.send_doctor_feedback(
            result.get('prescription_id', 'test_id'), 
            feedback_data
        )
        print(f"\nFeedback result: {feedback_result}")
        
        # Test model update
        logger.info("Testing model update...")
        update_result = await client.update_model()
        print(f"\nModel update result: {update_result}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())


