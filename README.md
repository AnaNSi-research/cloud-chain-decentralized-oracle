###### CLOUDCHAIN
A blockchain to handle accountability via smart contracts for clouds hosting files and clients reading/writing these files.
The network is run through polygon (or docker) and populated with the smart contracts via truffle.

DEPENDENCIES TO RUN CLOUDCHAIN:
** curl
** nvm (through curl via a download link)
nvm install v17.6.0
(If no node_modules folder is present in src) in src folder run npm install (installs all src dependencies) and then run npm install @chainlink/contracts --save

SETUP TO RUN CLOUDCHAIN:
> Go to polygon-nodes folder, and run in 5 separate terminals:
polygon-edge server --data-dir ./test-chain-1 --chain genesis.json --grpc :10000 --libp2p :10001 --jsonrpc :10002 --seal
polygon-edge server --data-dir ./test-chain-2 --chain genesis.json --grpc :20000 --libp2p :20001 --jsonrpc :20002 --seal
polygon-edge server --data-dir ./test-chain-3 --chain genesis.json --grpc :30000 --libp2p :30001 --jsonrpc :30002 --seal
polygon-edge server --data-dir ./test-chain-4 --chain genesis.json --grpc :40000 --libp2p :40001 --jsonrpc :40002 --seal
polygon-edge server --chain genesis.json --dev --log-level debug
> Go to src folder, and run in order in yet another terminal:
npx truffle migrate --reset --network polygon

npx truffle test --network polygon
> All tests should be visible in the last terminal, and should run properly besides tests 5 and 9;
> Go to src/contracts folder and rename CloudSLA.sol into something else and CloudSLA.test in CloudSLA.sol; Now rerunning tests
should be all good. This step detaches the cloudchain from the decentralized oracle (Chainlink): make sure to undo these changes when going into production.

TO RESTART CLOUDCHAIN WHERE IT LEFT OFF:
> Repeat SETUP steps

TO RESET AND RESTART CLOUDCHAIN:
> Delete all contents of polygon-nodes folder, then run the following in the same folder:
polygon-edge secrets init --data-dir test-chain-1
polygon-edge secrets init --data-dir test-chain-2
polygon-edge secrets init --data-dir test-chain-3
polygon-edge secrets init --data-dir test-chain-4
> Save the node ID and public key for each node in a file "init-data"
> Initialize the genesis.json file by running, after replacing $NODEID1, $NODEPUBLICADDR1, $NODEPUBLICADDR2, $NODEPUBLICADDR3, $NODEPUBLICADDR4:
polygon-edge genesis --consensus ibft --ibft-validators-prefix-path test-chain- --bootnode /ip4/127.0.0.1/tcp/10001/p2p/$NODEID1 --premine=$NODEPUBLICADDR1:1000000000000000000000 --premine=$NODEPUBLICADDR2:1000000000000000000000 --premine=$NODEPUBLICADDR3:1000000000000000000000 --premine=$NODEPUBLICADDR4:1000000000000000000000 --block-gas-limit 1000000000
> Continue with the first steps of "SETUP TO RUN BLOCKCHAIN", up until the "truffle migrate" command;
> Go to each nodes folder and in each open the consensus/validator.key file, and store the key in the "init-data" text file (these are the private keys). Replace with these addresses the addresses in file src/truffle-config.json file, in list "polygonPrivateKeys".

###### FILE DIGEST ORACLE
A decentralized oracle is used to check file hashes in order to ensure integrity, as an unbiased entity.
The Oracle is created via an hash-computing external adapter for Chainlink nodes, which is a blockchain of oracles.
You may think of the external adapter as a plugin for Chainlink nodes.

DEPENDENCIES TO RUN LOCALLY CHAINLINK EXTERNAL ADAPTER:
** yarn (through npm!)
(If no node_modules folder is present in chainlink-ext-adapter) in chainlink-ext-adapter folder run npm install (installs all adapter dependencies)

SETUP TO RUN LOCALLY CHAINLINK EXTERNAL ADAPTER:
> Go to chainlink-ext-adapter folder, and run in 2 separate terminals:
npx yarn start
curl -X POST -H "content-type:application/json" "http://localhost:8080/" --data '{ "id": 0, "data": { "url": "https://www.anticatrattoriadelreno.it/xml/menu-piatti.xml" } }'
> Response should in second terminal have code 200 and a hash as the result

###### CHAINLINK NODE
In order for the smart contracts to call upon the decentralized oracle, at least a Chainlink node must have the appropriate external adapter running. This can be done either by deploying the adapter in the Chainlink mainnet (the only option for production), in the Chainlink testnets, or finally by deploying a node ourselves and contacting it for operations. We do the latter.

** NOTE: The connection (SLA contract <-> Chainlink oracle) has never been tested in practice, so modifications may need to be applied.

DEPENDENCIES TO RUN CHAINLINK NODE:
sudo apt-get install postgresql
curl -sSL https://get.docker.com | sh
sudo systemctl start docker
sudo usermod -aG docker $USER
> A local or remote PC to run a postgreSQL database and the external adapter

SETUP TO RUN CHAINLINK NODE:
> Setup a local or remote postgreSQL server;
> Go to rinkeby-node folder and change in .env file the db username (default "chainlink-node"), db password (default "password") and ip address where the postgreSQL server is running. To check connectivity, run the line:
	psql -U $USERNAME -d $DBNAME -h $IPADDRESS
If console displays as postgreSQL username followed by "=#" then connection is successful.
> Once db server is up, in rinkeby-node folder run:
sudo docker run -p 6688:6688 -v rinkeby-node:/chainlink -it --env-file=.env smartcontract/chainlink:1.2.1 local n
This will download and run the Docker container with the Chainlink node.
> Create a store key (one is provided in the credentials file) as well as a API mail and password (again, one is provided, but you can choose your
own);
> To run the node, run the same line as before and enter the store key when asked. Node should now be running (requests can be checked via Alchemy, which is a website. Credentials are in the credentials file). Once node is running, GUI for Chainlink node can be accessed at localhost:6688/. Enter credentials and in the homepage find the public address of the node and save it;
> Replace under src/test/cloudsla.js the node address;
> Run the external adapter, either locally or remote, as detailed above and in the Chainlink GUI go to the Bridges tab, create a new bridge with name "sha256bridge" and as bridge URL the address in format http://$IP:$PORT (local or remote) where the external adapter is running through yarn;
> Go to the Jobs tab and create a new job with the following specification, replacing $NODEADDRESS with the Chainlink Ethereum node address:

type = "directrequest"
schemaVersion = 1
name = "sha 256 from url"
contractAddress = "$NODEADDRESS"
observationSource = """
    ds          [type="bridge" name="sha256bridge" requestData="{\\"data\\":{\\"url\\": $(url)}}"]

    ds
"""

Once the job has been created, copy the external job ID. Under src/contracts/CloudSLA.sol, replace the oracleData.jobId at line 189 with this value.

SETUP TO ADD ETH TO CHAINLINK NODE:
> Go to https://faucets.chain.link/rinkeby, connect the Metamask wallet. Only a limited amount per day can be obtained. Alternatively site https://faucets.chain.link/rinkeby can also be used, by first sending a tweet on the Twitter account with the node public address, and then requesting ETH by pasting the tweet link (may not work all the time). Once the wallet has received ETH, send it to chainlink node address (the address from the steps before) from Metamask.
