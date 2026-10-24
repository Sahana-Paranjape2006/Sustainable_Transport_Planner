
const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const co2Routes = require("./co2_e_routes");
app.use("/api/co2", co2Routes);

app.get("/", (req, res) => {
  res.send("CO2 Calculator API is running!");
});

const PORT = 5002;

const server = app.listen(PORT, () => {
  console.log(`CO2 server running at http://localhost:${PORT}`);
});

server.on("close", () => {
  console.log("Server has closed.");
});

server.on("error", (err) => {
  console.error("Server error:", err.message);
});
