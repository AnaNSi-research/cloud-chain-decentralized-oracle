var FileDigestOracle = artifacts.require('FileDigestOracle');
var Factory = artifacts.require('Factory');

module.exports = async function (deployer, network, addresses) {
  await deployer.deploy(FileDigestOracle, { from: addresses[2] });
  await deployer.deploy(Factory);
};
