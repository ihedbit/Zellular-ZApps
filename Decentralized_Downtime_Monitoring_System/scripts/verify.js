const hre = require("hardhat");

async function main() {
  const contractAddress = "YOUR_CONTRACT_ADDRESS";
  const constructorArgs = ["ARG1", "ARG2"];

  await hre.run("verify:verify", {
    address: contractAddress,
    constructorArguments: constructorArgs,
  });
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
