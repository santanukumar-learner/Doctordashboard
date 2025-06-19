const express=require("express");
const app= express();
const path = require("path");
const mongoose = require("mongoose");
const session = require("express-session");
const flash = require("connect-flash");
const bcrypt = require("bcrypt");
// const Reporter=require("./models/reporter")
//const Hazard=require("./models/hazard");
const frontdesk=require("./models/frontdesk");
const { generateToken, verifyToken } = require("./middleware/isloggedin.js");
const cookieParser = require("cookie-parser");
const nodemailer = require("nodemailer");
const multer = require("multer");
const Doctor = require('./models/doctors');
const fs = require('fs');
const { GoogleGenerativeAI } = require('@google/generative-ai');

app.set("view engine", "ejs");
app.use(cookieParser());
app.use(express.static(path.join(__dirname, "public")));
app.use(express.urlencoded({ extended: true }));
app.use(express.json()); 
app.use(express.static("uploads"));
app.use(
    session({
        secret: "your_secret_key",
        resave: false,
        saveUninitialized: false
    })
);
app.use(flash());



app.use((req, res, next) => {
  res.locals.success = req.flash("success");
  res.locals.error = req.flash("error");
  res.locals.welcome = req.flash("welcome");
  next();
});




app.use((req, res, next) => {
  console.log("Session contents:", req.session);
  next();
});






// Image upload (assuming you already have this)
const imageStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'public/uploads/');
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});
const uploadImage = multer({ storage: imageStorage });





// Audio upload
const audioStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadPath = path.join(__dirname, 'public/audio');
    fs.mkdirSync(uploadPath, { recursive: true });
    cb(null, uploadPath);
  },
  filename: function (req, file, cb) {
    const filename = `audio-${Date.now()}.webm`;
    cb(null, filename);
  }
});
const uploadAudio = multer({ storage: audioStorage });

//mongodb connection

mongoose.connect("mongodb://127.0.0.1:27017/Clinic", {
    useNewUrlParser: true,
    useUnifiedTopology: true
})
.then(() => console.log("Connected to MongoDB"))
.catch(err => console.log("MongoDB Connection Error:", err));

app.get("/",(req,res)=>{
     res.render("home");

});

app.get("/login", (req, res) => {
    const formData = req.flash("formData")[0] || {};
    const error = req.flash("error")[0];
    console.log("Flash error received at /login:", error);

    res.render("login", {
        formData,
        error
    });
});



//post register

app.post("/register", async (req, res) => {
    try {
        const { fullname, email, phone, password } = req.body;

        // 🔍 Check if user already exists
        const existingUser = await frontdesk.findOne({
            $or: [{ email }, { phone }]
        });
       // console.log(existingUser);

       if (existingUser) {
    req.flash("error", "Email or phone number already registered!");
    req.flash("formData", { fullname, email, phone });
    console.log("Set flash error:", "Email or phone number already registered!");
    return res.redirect("/login");
}


        const hashedPassword = await bcrypt.hash(password, 10);
        const newUser = new frontdesk({
            fullname,
            email,
            phone,
            password: hashedPassword
        });

        console.log(newUser);


        await newUser.save();
          req.session.frontdeskId = newUser._id;
        //  console.log(newUser._id);
        //  console.log(req.session.reporterId);



          // await Reporter.findOneAndUpdate({ email: 'swarajnitrkl@gmail.com' }, { role: 'admin' });


        const token = generateToken(newUser);
        res.cookie("token", token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            maxAge: 2 * 60 * 60 * 1000,
        });

        // ✅ Send welcome email
        const transporter = nodemailer.createTransport({
            service: "gmail",
            auth: {
                user: "swarajnitrkl@gmail.com",
                pass: "jtik znfb krqf qlyj"
            }
        });

        const mailOptions = {
            from: "swarajnitrkl@gmail.com",
            to: email,
            subject: "Welcome to Our Platform!",
            text: `Hi ${fullname},\n\nThanks for registering with us! We're excited to have you on board.`
        };

        transporter.sendMail(mailOptions, (error, info) => {
            if (error) {
                console.error("Email send error:", error);
            } else {
                console.log("Email sent:", info.response);
            }
        });

        req.flash("success", "Registration successful! Welcome.");
        res.render("post_home"); // 🔁 update this to your actual post-login route

    } catch (error) {
        console.error("Registration error:", error);
        req.flash("error", "Something went wrong. Please try again.");
        res.redirect("/login");
    }
});



//post login
app.post("/login", async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = await frontdesk.findOne({ email });

        if (!user) {
            req.flash("error", "User not found");
            return res.status(401).json({ message: "User not found" });
        }

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            req.flash("error", "Invalid credentials");
            return res.status(401).json({ message: "Invalid credentials" });
        }
         req.session.frontdeskId = newUser._id;

        // ✅ Generate JWT Token
        const token = generateToken(user);

        // ✅ Set the token as a cookie (HTTP-only for security)
        res.cookie("token", token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production", // ✅ Secure in production
            maxAge: 2 * 60 * 60 * 1000, // ✅ 2 hours expiry
        });

        req.flash("welcome", `Welcome back, ${user.username}!`);
        res.render("post_home"); // ✅ Redirect without `{ token }`
    } catch (error) {
        res.status(500).json({ error: "Error logging in" });
    }
}); 


//logout

app.get("/logout", (req, res) => {
    res.clearCookie("token"); // ✅ Remove JWT Cookie
    req.session.destroy((err) => { // ✅ Destroy session (if any)
        if (err) {
            console.error("Session destruction error:", err);
            return res.redirect("/");
        }
        res.redirect("/"); // ✅ Redirect to login page after logout
    });
});


//post home
app.get("/home",verifyToken,  (req, res) => {
    const user = req.user;
    if(user){
        res.render("post_home", { user: req.user });
    }
    else{
        res.render("home");
    }
});





////////////////////////////////////////doctor page///////////////////////////////////////////////////////////////////////
app.get('/doctors', verifyToken, async (req, res) => {
  const user = req.user;
  if (!user) {
    return res.render("home");
  }

  try {
    const doctors = await Doctor.find(); // Fetch all doctors from DB
    res.render('doctors', {
      user: user,
      doctors: doctors // Send all doctors to the template
    });
  } catch (err) {
    console.error("Error fetching doctors:", err);
    res.status(500).send("Internal Server Error");
  }
});

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

app.get('/add-doctor', verifyToken, (req, res) => {
  const user =req.user;
  if(!user){
    return res.render("home");
  }
    res.render('add-doctor', { user: req.user }); // Pass user info if needed
});
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
app.get('/add-patient', verifyToken, (req, res) => {
  const user =req.user;
  if(!user){
    return res.render("home");
  }
    res.render('add-patient', { user: req.user }); // Pass user info if needed
});




//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

app.get('/post_home', verifyToken, (req, res) => {
  const user =req.user;
  if(!user){
    return res.render("home");
  }
    res.render('post_home', { user: req.user }); // Pass user info if needed
});


////////////////////////////////////////////////////////////////////////////////////////////////////////////////


app.post('/add-doctor', uploadImage.single('profilePicture'), async (req, res) => {
    try {
        const {
          doctorNumber,
            name,
            gender,
            phone,
            email,
            specialization,
            experience,
            qualifications,
            availableDays,
            ratings,
            availableTime
        } = req.body;

        const newDoctor = new Doctor({
          doctorNumber,
            name,
            gender,
            phone,
            email,
            specialization,
            experience,
            qualifications: Array.isArray(qualifications) ? qualifications : [qualifications],
            availableDays: Array.isArray(availableDays) ? availableDays : [availableDays],
            ratings: parseFloat(ratings) || 0,
            availableTime,
            profilePicture: req.file ? '/uploads/' + req.file.filename : ''
        });

        await newDoctor.save();
        res.redirect('/post_home'); // or wherever you want to go after adding
    } catch (error) {
        console.error('Error adding doctor:', error);
        res.status(500).send('Server error while adding doctor.');
    }
});



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

app.get('/doctor/:id/schedule', async (req, res) => {
  const doctor = await Doctor.findById(req.params.id);
  if (!doctor) return res.status(404).send("Doctor not found");

  res.render('schedule', { doctor });
});
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////





///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
const genAI = new GoogleGenerativeAI('AIzaSyCyC2NLGoy9aD4b3nPXDoXNbSskrQ5hsBE');

async function askGemini(promptText) {
 const model = genAI.getGenerativeModel({
   model: "gemini-2.0-flash",

  });
  console.log(model);
  


  const result = await model.generateContent(promptText);
  console.log(result);
  const response = await result.response;
  const text = await response.text();

  return text;
}

const { exec } = require('child_process');

app.post('/upload-audio', uploadAudio.single('audio'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ message: 'No file uploaded' });
  }

  const audioPath = path.join(__dirname, 'public', 'audio', req.file.filename);

  exec(`python transcribe.py "${audioPath}"`, async (error, stdout, stderr) => {
    if (error) {
      console.error('Transcription error:', stderr);
      return res.status(500).json({ message: 'Error during transcription' });
    }

    const transcription = stdout.trim();
    console.log('Transcribed Text:', transcription);

    function extractJson(text) {
      const match = text.match(/```json\s*([\s\S]*?)\s*```/i) || text.match(/({[\s\S]*})/);
      return match ? match[1] : null;
    }

    try {
      const geminiResponse = await askGemini(`
        Extract the following details from this text and return them strictly as a JSON dictionary:
        - "dn": doctor number(return a integer)
        - "pn": patient number(return a integer)
        - "ds": disease
        - "time": appointment time (in 12 hour format and add AM or PM)

        Text: "${transcription}"

        Only return the JSON dictionary. Do not include any explanation or extra text.
      `);

      const jsonString = extractJson(geminiResponse);
      if (!jsonString) throw new Error("No JSON found in Gemini response");

      const parsed = JSON.parse(jsonString);
      const { dn, pn, ds, time } = parsed;

      console.log("Doctor Number (dn):", dn);
      console.log("Patient Number (pn):", pn);
      console.log("Disease (ds):", ds);
      console.log("Appointment Time:", time);

      const today = new Date();

      // 🧑‍⚕️ Fetch doctor by doctor number
      const doctor = await Doctor.findOne({ doctorNumber: dn });
     // console.log("doctor hu mai",doctor);
      if (!doctor) {
        return res.status(404).json({ message: 'Doctor not found' });
      }

      // 🧑‍🦰 Fetch patient by patient number
      const patient = await Patient.findOne({ patientNumber: pn });
     // console.log("patient hu main",patient);
      if (!patient) {
        return res.status(404).json({ message: 'Patient not found' });
      }

      const dateString = today.toISOString().split('T')[0];
      let dateEntry = doctor.schedule.find(entry => entry.date.toISOString().split('T')[0] === dateString);

      if (!dateEntry) {
        dateEntry = {
          date: today,
          appointments: []
        };
        doctor.schedule.push(dateEntry);
      }

      // Add new appointment with patient's ObjectId
      console.log(patient._id);

      dateEntry.appointments.push({
        patient: patient._id,
        time,
        status: 'Scheduled'
      });

      await doctor.save();

      res.json({
        transcription,
        data: parsed,
        message: 'Appointment added to doctor schedule successfully'
      });

    } catch (err) {
      console.error('Error querying Gemini or updating DB:', err.message);
      res.status(500).json({ message: 'Error processing appointment' });
    }
  });
});

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
const Patient = require('./models/patient');

const patientUpload = uploadImage.fields([
  { name: 'profilePicture', maxCount: 1 },
  { name: 'medicalHistory', maxCount: 10 }
]);

app.post('/add-patients', patientUpload, async (req, res) => {
  try {
    const {
      patientNumber,
      name,
      contactNumber,
      email,
      age,
      gender,
      bloodGroup,
      address
    } = req.body;

    // Extract profile picture filename
    const profilePicture = req.files['profilePicture']?.[0]?.filename || '';

    // Map medicalHistory files to objects with documentName and fileUrl
    const medicalHistory = (req.files['medicalHistory'] || []).map(file => ({
      documentName: file.originalname,
      fileUrl: file.filename,
    }));

    const newPatient = new Patient({
      patientNumber,
      name,
      contactNumber,
      email,
      age,
      gender,
      bloodGroup,
      address,
      profilePicture,
      medicalHistory
    });

    await newPatient.save();

    res.status(201).send('Patient added successfully!');
  } catch (err) {
    console.error('Error adding patient:', err);
    res.status(500).send('Error saving patient');
  }
});

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
app.get('/login-doctor', (req, res) => {
  res.render('login-doctor');
});


app.post('/doctor/contact', async (req, res) => {
  const { phone, email } = req.body;

  try {
    const doctor = await Doctor.findOne({ phone, email })
      .populate({
        path: 'schedule.appointments.patient',
        model: 'Patient'
      });

    if (doctor) {
      res.render('doc-dashboard', { doctor });
    } else {
      res.status(401).send('Doctor not found.');
    }
  } catch (error) {
    console.error(error);
    res.status(500).send('Server Error');
  }
});
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
app.get('/add-symptoms', (req, res) => {
  const patientId = req.query.patientId;
  // Fetch patient data if needed
  res.render('add-symptoms', { patientId });
});

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

const axios = require('axios');


const WebSocket = require('ws');

function sendToMCPServer(patientInput) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket('ws://localhost:8765'); 

    ws.on('open', () => {
      console.log('🔗 Connected to Python MCP Server');

      const data = {
        type: 'generate_prescription',
        patient_input: patientInput
      };

      ws.send(JSON.stringify(data));
    });

    ws.on('message', (message) => {
      const response = JSON.parse(message);

      if (response.type === 'prescription_generated') {
        resolve(response); // send prescription back
      } else {
        reject(new Error(response.message || 'Unknown error'));
      }

      ws.close(); // close connection after response
      console.log("hi");
    });

    ws.on('error', (err) => {
      reject(err);
    });

    ws.on('close', () => {
      console.log('❌ Connection to MCP Server closed');
    });
  });
}



app.post('/submit-symptoms', async (req, res) => {
  const { gender, age, symptoms, diagnosis, name } = req.body;

  const patientInput = {
    name: name || 'Anonymous',
    age: parseInt(age),
    gender,
    diagnosis,
    symptoms: Array.isArray(symptoms) ? symptoms : symptoms.split(',').map(s => s.trim())
  };

  try {
    const response = await sendToMCPServer(patientInput);
    console.log(response);

    const prescription = response.prescription;

    // Render only the medications list
   res.render('symptoms-result', {
  medications: prescription.medications || [],
  patientName: prescription.patient_name,
  prescriptionId: response.prescription_id,
  age: age,
  gender:gender
});

  } catch (err) {
    console.error('⚠️ Error communicating with MCP server:', err);
    res.status(500).send("Server error: Unable to generate prescription");
  }
});
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
const PDFDocument = require('pdfkit');

app.post('/generate-pdf', (req, res) => {
  const { patientName, prescriptionId, medications } = req.body;
  const medList = medications.split('\n').map(med => med.trim()).filter(Boolean);

  const doc = new PDFDocument();
  const filePath = `./public/prescriptions/${prescriptionId}.pdf`;

  // Ensure the directory exists
  fs.mkdirSync('./public/prescriptions', { recursive: true });

  const stream = fs.createWriteStream(filePath);
  doc.pipe(stream);

  doc.fontSize(20).text('Prescription', { align: 'center' });
  doc.moveDown();
  doc.fontSize(12).text(`Patient Name: ${patientName}`);
  doc.text(`Prescription ID: ${prescriptionId}`);
  doc.moveDown();

  doc.fontSize(14).text('Medications:', { underline: true });
  medList.forEach((med, index) => {
    doc.fontSize(12).text(`${index + 1}. ${med}`);
  });

  doc.end();

  stream.on('finish', () => {
    res.download(filePath, `${patientName}_prescription.pdf`);
  });
});

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////passport setup  //////////////////

const passport = require("passport");
require("./passport-config"); // import passport config

//const session = require("express-session");
//app.use(session({ secret: "secret", resave: false, saveUninitialized: false }));
app.use(passport.initialize());
app.use(passport.session());




app.get("/auth/google",
  passport.authenticate("google", { scope: ["profile", "email"] })
);

app.get("/auth/google/callback",
  passport.authenticate("google", { failureRedirect: "/login" }),
  (req, res) => {
    const token = generateToken(req.user);
    res.cookie("token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      maxAge: 2 * 60 * 60 * 1000,
    });
    res.redirect("/home");
  }
);


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

app.listen(3000,()=>console.log("app is listining"));
