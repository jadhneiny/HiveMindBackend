const { Pool } = require("pg");
require("dotenv").config({ path: "database.env" });

// Create a pool instance for PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: false, // Required for Neon database connections
  },
});

// Query wrapper to interact with the database
const query = (text, params) => pool.query(text, params);

// Example: Fetch all users
const getUsers = async () => {
  try {
    const result = await query("SELECT * FROM users");
    return result.rows;
  } catch (err) {
    console.error("Error fetching users from DB:", err);
    throw err;
  }
};

// Example: Add a user to the database
const addUser = async (username, email, password) => {
  try {
    const result = await query(
      "INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING *",
      [username, email, password]
    );
    return result.rows[0];
  } catch (err) {
    console.error("Error adding user:", err);
    throw err;
  }
};

module.exports = { query, getUsers, addUser };
