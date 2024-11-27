const express = require("express");
const app = express();

// Middleware for parsing JSON
app.use(express.json());

// Example Route
app.get("/", (req, res) => {
  res.send("Hello from HiveMind Backend!");
});

// Example POST route
app.post("/api/register", (req, res) => {
  const { username, email } = req.body;
  res.json({ message: `User ${username} registered with email: ${email}` });
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app; // For Vercel
//test