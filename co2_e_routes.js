
const express = require("express");
const {
  VEHICLES,
  calculateEmission,
} = require("./co2_e");

const router = express.Router();

// Get all vehicles
router.get("/vehicles", (req, res) => {
  const vehicles = Object.entries(VEHICLES).map(
    ([vehicleType, vehicle]) => ({
      vehicleType: vehicleType,
      label: vehicle.label,
      emissionFactor: vehicle.factor,
    })
  );

  res.json({ vehicles });
});

// Calculate emissions
router.post("/calculate", (req, res) => {
  try {
    const result = calculateEmission(req.body);

    res.json({
      success: true,
      result: result,
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: error.message,
    });
  }
});

module.exports = router;
