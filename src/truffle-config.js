const dotenv = require('dotenv');
const HDWalletProvider = require('truffle-hdwallet-provider');
const Web3 = require('web3');
const wsProvider = new Web3.providers.WebsocketProvider('ws://localhost:8546');
const httpProvider = new Web3.providers.HttpProvider('http://localhost:8545');

// insert the private key of the accounts
// address of account 0 (12 in metamask) : 0xFE3B557E8Fb62b89F4916B721be55cEb828dBd73
dotenv.config();
/*
const privateKeys = [
  '0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63',
  '0xc87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3',
  '0xae6ae8e5ccbfb04590405997ee2d52d2b330726137b875053c36d94e974d162f',
];
*/
const polygonPrivateKeys = [
  '0x59c82efe6394a61d619f61e2fed5c8cbdaf1d0266be5da2cfb43b99d7c7ef026',
  '0x0a12cd3293cd0eac3a68712ab02f8c332c865e314d00e830e805ad828e5fd093',
  '0x722cfa8df6a2cfff1b5e754955b59b64eab0c0970324ef8aa958da316d571535',
  '0x829cadc45fc1133496d8454627907ad777e6f2a3145fa1ddd2ca8dc9522de0b0',
];

module.exports = {
  // See <http://truffleframework.com/docs/advanced/configuration>
  // for more about customizing your Truffle configuration!
  networks: {
    development: {
      host: '127.0.0.1',
      port: 8545,
      network_id: '*', // Match any network id
      gasPrice: 0,
    },
    quickstartWallet: {
      provider: () => {
        HDWalletProvider.prototype.on = wsProvider.on.bind(wsProvider);
        return new HDWalletProvider(privateKeys, wsProvider, 0, 3);
      },
      network_id: '*',
      gasPrice: 0,
      type: 'quorum',
      websockets: true,
    },
    polygon: {
      provider: () =>
        new HDWalletProvider(polygonPrivateKeys, httpProvider, 0, 3),
      network_id: '*',
      type: 'quorum',
      gasPrice: 0,
    },
  },
  compilers: {
    solc: {
      version: '0.8.9', // Fetch exact version from solc-bin (default: truffle's version)
      // docker: true,        // Use "0.5.1" you've installed locally with docker (default: false)
      // settings: {          // See the solidity docs for advice about optimization and evmVersion
      //  optimizer: {
      //    enabled: false,
      //    runs: 200
      //  },
      evmVersion: 'byzantium',
      // }
    },
  },
};
