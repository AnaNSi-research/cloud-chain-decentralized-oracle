# cloud-chain-simulation

## Blockchains used

We used three different kinds of blockchains with a default number of validator node that it's equal to 4. Other parameters equal for all configurations are the follow:

- Gas limit: 0xf7b760
- Block period seconds: 5

### Hyperledger Besu

- Setup: [https://consensys.net/quorum/products/guides/getting-started-with-consensys-quorum/](https://consensys.net/quorum/products/guides/getting-started-with-consensys-quorum/)

- Configuration: QBFT, IBFT, CLIQUE
  - Change `BESU_CONS_ALGO` variable in the *.env* file, inside the root directory.

### Go-Quorum

- Setup: [https://consensys.net/quorum/products/guides/getting-started-with-consensys-quorum/](https://consensys.net/quorum/products/guides/getting-started-with-consensys-quorum/)

- Configuration: qbft, instanbul, raft
  - Change `GOQUORUM_CONS_ALGO` variable in the *.env* file, inside the root directory.

### Polygon

- Setup: execute the script [*run_polygon.sh*](https://github.com/cotus997/cloud-chain-simulation/blob/main/polygon/run_polygon.sh), follow the instructions carefully because we don't handle any typing errors.

- Configuration: IBFT, PoS
