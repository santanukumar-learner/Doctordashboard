const mongoose = require('mongoose');

const doctorSchema = new mongoose.Schema({
    doctorNumber: {
        type: Number,
        required: true,
        unique: true,
        
    },
    name: {
        type: String,
        required: true,
        trim: true
    },
    specialization: {
        type: String,
        required: true,
        trim: true
    },
    experience: {
        type: Number,
        required: true,
        min: 0
    },
    phone: {
        type: String,
        required: true,
        match: /^[0-9]{10}$/
    },
    email: {
        type: String,
        required: true,
        unique: true,
        lowercase: true
    },
    gender: {
        type: String,
        enum: ['Male', 'Female', 'Other'],
        required: true
    },
    qualifications: {
        type: [String],
        required: true
    },
    availableDays: {
        type: [String],
        default: []
    },
    availableTime: {
        start: { type: String },
        end: { type: String }
    },
    ratings: {
        type: Number,
        min: 0,
        max: 5,
        default: 0
    },
    profilePicture: {
        type: String,
        default: ''
    },
    schedule: [
        {
            date: { type: Date, required: true },
            appointments: [
                {
                    patient: {
                        type: mongoose.Schema.Types.ObjectId,
                        ref: 'Patient',
                        required: true
                    },
                    time: { type: String, required: true },
                    status: {
                        type: String,
                        enum: ['Scheduled', 'Completed', 'Cancelled'],
                        default: 'Scheduled'
                    }
                }
            ]
        }
    ],
    createdAt: {
        type: Date,
        default: Date.now
    }
});

const Doctor = mongoose.model('Doctor', doctorSchema);

module.exports = Doctor;
