const { ethers } = require("hardhat");

async function main() {
  const AVS = await ethers.getContractFactory("AVS");
  const avs = await AVS.deploy();

  await avs.deployed();
  console.log("AVS contract deployed to:", avs.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
