const { ethers } = require("hardhat");

async function main() {
  const avsAddress = "YOUR_CONTRACT_ADDRESS";
  const avs = await ethers.getContractAt("AVS", avsAddress);

  const activeOperators = await avs.getActiveOperators();
  console.log("Active Operators:", activeOperators);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
