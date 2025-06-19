const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
    console.log('🟢 Connected to MCP Server');

    // Example patient data
    const data = {
        type: 'generate_prescription',
        patient_input: {
            name: "Alice Johnson",
            age: 32,
            gender: "female",
            diagnosis: "headach",
            symptoms: ["sore throat", "cough", "fever"]
        }
    };

    // Send to Python server
    ws.send(JSON.stringify(data));
});

ws.on('message', (message) => {
    const response = JSON.parse(message);
    console.log('📥 Received from server:', response);

    if (response.type === 'prescription_generated') {
        console.log('✅ Prescription Generated!');
        console.log(JSON.stringify(response.prescription, null, 2));
    } else if (response.type === 'error') {
        console.error('❌ Error:', response.message);
    }
});

ws.on('close', () => {
    console.log('🔴 Disconnected from server');
});

ws.on('error', (error) => {
    console.error('❗ WebSocket Error:', error);
});


