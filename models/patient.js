const mongoose = require('mongoose');

const patientSchema = new mongoose.Schema({
  patientNumber: {
    type: Number,
    required: true,
    unique: true,
    
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  contactNumber: {
    type: String,
    required: true,
    match: /^[0-9]{10}$/, // Basic 10-digit validation
    trim: true
  },
  email: {
    type: String,
    required: true,
    lowercase: true,
    unique: true
  },
  age: {
    type: Number,
    required: true,
    min: 0
  },
  gender: {
    type: String,
    enum: ['Male', 'Female', 'Other'],
    required: true
  },
  address: {
    type: String,
    default: ''
  },
  emergencyContact: {
    name: String,
    phone: {
      type: String,
      match: /^[0-9]{10}$/
    },
    relation: String
  },
  medicalHistory: [
    {
      //documentName: { type: String, required: true },
      fileUrl: { type: String, required: true }, // Path to PDF stored in server/cloud
     // uploadedAt: { type: Date, default: Date.now }
    }
  ],
  profilePicture: {
    type: String,
    default: '' // Optional image path
  },
  bloodGroup: {
    type: String,
    enum: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown'],
    default: 'Unknown'
  },
  allergies: {
    type: [String],
    default: []
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

const Patient = mongoose.model('Patient', patientSchema);

module.exports = Patient;
