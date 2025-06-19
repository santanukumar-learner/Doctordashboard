#!/usr/bin/env python3
"""
Simple example of using the MCP Medical System
Run this after starting the server
"""

import asyncio
import json
from ..client.mcp_client import MCPClient

async def simple_example():
    """Simple example of using the MCP system"""
    
    # Create client instance
    client = MCPClient("ws://localhost:8765")
    
    print("🏥 MCP Medical System Example")
    print("-" * 40)
    
    try:
        # Step 1: Connect to server
        print("1. Connecting to server...")
        if not await client.connect():
            print("❌ Failed to connect to server")
            print("   Make sure the server is running!")
            return
        print("✅ Connected successfully")
        
        # Step 2: Prepare patient data
        print("\n2. Preparing patient data...")
        patient_data = {
            "name": "John Smith",
            "age": 45,
            "medical_history": ["hypertension", "diabetes"],
            "allergies": ["penicillin", "shellfish"]
        }
        
        symptoms = ["fever", "headache", "body ache", "fatigue"]
        
        print(f"   Patient: {patient_data['name']}, Age: {patient_data['age']}")
        print(f"   Symptoms: {', '.join(symptoms)}")
        print(f"   Medical History: {', '.join(patient_data['medical_history'])}")
        print(f"   Allergies: {', '.join(patient_data['allergies'])}")
        
        # Step 3: Generate prescription
        print("\n3. Generating prescription...")
        result = await client.generate_prescription(patient_data, symptoms)
        
        if result.get("status") == "success":
            print("✅ Prescription generated successfully!")
            
            # Display prescription details
            prescription = result.get("prescription", {})
            prescription_id = result.get("prescription_id")
            
            print(f"\n📋 Prescription ID: {prescription_id}")
            print(f"   Patient: {prescription.get('patient_name')}")
            print(f"   Generated: {prescription.get('generated_at')}")
            
            print("\n💊 Medications:")
            for i, med in enumerate(prescription.get("medications", []), 1):
                print(f"   {i}. {med['name']} - {med['dosage']}")
                print(f"      Take: {med['frequency']} for {med['duration']}")
                print(f"      Reason: {med['reason']}")
            
            print(f"\n📝 Notes: {prescription.get('notes')}")
            
            # Step 4: Send doctor feedback
            print("\n4. Sending doctor feedback...")
            feedback_data = {
                "original_prescription": prescription,
                "modified_prescription": {
                    "medications": prescription.get("medications", []),
                    "additional_notes": "Approved with no changes"
                },
                "feedback_notes": "Prescription looks good. Patient should monitor blood pressure due to medical history.",
                "doctor_id": "DR001",
                "patient_input": patient_data
            }
            
            feedback_result = await client.send_doctor_feedback(prescription_id, feedback_data)
            
            if feedback_result.get("status") == "success":
                print("✅ Doctor feedback sent successfully!")
                print(f"   Feedback ID: {feedback_result.get('feedback_id')}")
            else:
                print(f"❌ Error sending feedback: {feedback_result.get('message')}")
            
            # Step 5: Update model (optional)
            print("\n5. Requesting model update...")
            update_result = await client.update_model()
            
            if update_result.get("status") == "success":
                print("✅ Model update completed!")
                print(f"   New version: {update_result.get('new_version')}")
                print(f"   Updated at: {update_result.get('updated_at')}")
            else:
                print(f"❌ Error updating model: {update_result.get('message')}")
        
        else:
            print(f"❌ Error generating prescription: {result.get('message')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Step 6: Disconnect
        print("\n6. Disconnecting...")
        await client.disconnect()
        print("✅ Disconnected from server")

async def interactive_example():
    """Interactive example where user provides input"""
    
    client = MCPClient("ws://localhost:8765")
    
    print("🏥 Interactive MCP Medical System")
    print("-" * 40)
    
    try:
        if not await client.connect():
            print("❌ Failed to connect to server")
            return
        
        print("✅ Connected to server")
        
        # Get user input
        print("\nEnter patient information:")
        name = input("Patient name: ").strip()
        age = int(input("Patient age: "))
        
        print("\nEnter symptoms (comma-separated):")
        symptoms_input = input("Symptoms: ").strip()
        symptoms = [s.strip() for s in symptoms_input.split(",") if s.strip()]
        
        print("\nEnter medical history (comma-separated, or press Enter to skip):")
        history_input = input("Medical history: ").strip()
        medical_history = [h.strip() for h in history_input.split(",") if h.strip()] if history_input else []
        
        print("\nEnter allergies (comma-separated, or press Enter to skip):")
        allergies_input = input("Allergies: ").strip()
        allergies = [a.strip() for a in allergies_input.split(",") if a.strip()] if allergies_input else []
        
        # Prepare data
        patient_data = {
            "name": name,
            "age": age,
            "medical_history": medical_history,
            "allergies": allergies
        }
        
        # Generate prescription
        print(f"\nGenerating prescription for {name}...")
        result = await client.generate_prescription(patient_data, symptoms)
        
        if result.get("status") == "success":
            prescription = result.get("prescription", {})
            print("\n" + "="*50)
            print("PRESCRIPTION GENERATED")
            print("="*50)
            print(json.dumps(prescription, indent=2))
        else:
            print(f"Error: {result.get('message')}")
    
    except ValueError:
        print("❌ Invalid input. Please enter a valid age.")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.disconnect()

def main():
    """Main function to choose example type"""
    print("Choose an example:")
    print("1. Simple automated example")
    print("2. Interactive example")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\nRunning simple automated example...")
        asyncio.run(simple_example())
    elif choice == "2":
        print("\nRunning interactive example...")
        asyncio.run(interactive_example())
    else:
        print("Invalid choice. Running simple example...")
        asyncio.run(simple_example())

if __name__ == "__main__":
    main()