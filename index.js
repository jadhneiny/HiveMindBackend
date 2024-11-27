const express = require("express");
const app = express();
require("dotenv").config({ path: "database.env" }); // Load .env variables

// Middleware for parsing JSON
app.use(express.json());

// Import database functions
const { query, getUsers, addUser } = require("./db");

// Example Home Route
app.get("/", (req, res) => {
  res.send("Hello from HiveMind Backend!");
});

// Route: Fetch all users
app.get("/api/users", async (req, res) => {
  console.log("GET /api/users called");

  try {
    const users = await getUsers();
    res.json(users);
  } catch (err) {
    console.error("Error fetching users:", err); // Log the detailed error
    res.status(500).json({ error: "Failed to fetch users" });
  }
});

// Route: Register a user
app.post("/api/register", async (req, res) => {
  const { username, email, password } = req.body;

  if (!username || !email || !password) {
    return res.status(400).json({ error: "All fields are required" });
  }

  try {
    const newUser = await addUser(username, email, password);
    res.status(201).json({ message: "User registered successfully", user: newUser });
  } catch (err) {
    res.status(500).json({ error: "Failed to register user" });
  }
});

// Test Database Connection
(async () => {
  try {
    const res = await query("SELECT NOW()");
    console.log("Database connected:", res.rows[0]);
  } catch (err) {
    console.error("Database connection error:", err);
  }
})();

// Start the server
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// console.log("Database URL:", process.env.DATABASE_URL); // Commented out for security
//was initially used for testing and debugging
module.exports = app; // For Vercel
