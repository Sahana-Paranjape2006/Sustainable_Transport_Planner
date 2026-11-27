
const VEHICLES = {
  car_petrol: { label: "Petrol Car", factor: 0.192 },
  car_diesel: { label: "Diesel Car", factor: 0.171 },
  car_hybrid: { label: "Hybrid Car", factor: 0.105 },
  car_electric: { label: "Electric Car", factor: 0.053 },
  motorcycle_petrol: { label: "Petrol Motorcycle", factor: 0.072 },
  bus_diesel: { label: "Diesel Bus", factor: 0.089 },
  metro_electric: { label: "Metro", factor: 0.035 },
  bicycle: { label: "Bicycle", factor: 0 },
  walking: { label: "Walking", factor: 0 },
};

function rateEmissionIntensity(kgCO2PerPassengerKm) {
  if (kgCO2PerPassengerKm === 0) {
    return { score: "A+", label: "Zero estimated emissions" };
  }
  if (kgCO2PerPassengerKm <= 0.05) {
    return { score: "A", label: "Very low emissions" };
  }
  if (kgCO2PerPassengerKm <= 0.10) {
    return { score: "B", label: "Low emissions" };
  }
  if (kgCO2PerPassengerKm <= 0.15) {
    return { score: "C", label: "Moderate emissions" };
  }
  if (kgCO2PerPassengerKm <= 0.20) {
    return { score: "D", label: "High emissions" };
  }
  return { score: "E", label: "Very high emissions" };
}

function calculateEmission({
  vehicleType,
  distanceKm,
  passengers = 1,
}) {
  const vehicle = VEHICLES[vehicleType];

  if (!vehicle) {
    throw new Error("Invalid vehicle type.");
  }

  const distance = Number(distanceKm);
  const people = Number(passengers);

  if (!Number.isFinite(distance) || distance < 0) {
    throw new Error("Distance must be zero or greater.");
  }

  if (!Number.isInteger(people) || people < 1) {
    throw new Error("Passengers must be a positive whole number.");
  }

  const totalKgCO2 = distance * vehicle.factor;
  const perPassengerKgCO2 = totalKgCO2 / people;
  const intensity =
    distance > 0 ? perPassengerKgCO2 / distance : vehicle.factor / people;

  return {
    vehicle: vehicle.label,
    distanceKm: distance,
    passengers: people,
    totalKgCO2: Number(totalKgCO2.toFixed(3)),
    perPassengerKgCO2: Number(perPassengerKgCO2.toFixed(3)),
    rating: rateEmissionIntensity(intensity),
  };
}

module.exports = {
  VEHICLES,
  calculateEmission,
  rateEmissionIntensity,
};
