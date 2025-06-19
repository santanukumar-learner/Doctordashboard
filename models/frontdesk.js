const mongoose = require('mongoose');

const frontdeskSchema = new mongoose.Schema({
  fullname: String,
  email: String,
  phone: String,
  password: String,
  googleId: String,

  // Reference to reported hazards
//   reportedHazards: [
//     {
//       type: mongoose.Schema.Types.ObjectId,
//       ref: 'Hazard'
//     }
//   ],
 
});

// ✅ Create 2dsphere index for location field


module.exports = mongoose.model('frontdesk', frontdeskSchema);
