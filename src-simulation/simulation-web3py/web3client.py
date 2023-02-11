import json
import os

from eth_typing import ChecksumAddress, Address
from semantic_version import Version
from solcx import install_solc, set_solc_version, compile_files, get_installed_solc_versions
from web3 import Web3, AsyncHTTPProvider, HTTPProvider
from web3.eth import AsyncEth

from settings import HTTP_URI, SOLC_VERSION, CONFIG_DIR
from utility import get_credentials


class Web3Client:
    def __init__(self, blockchain: str):
        self.w3_async = Web3(
            AsyncHTTPProvider(HTTP_URI),
            modules={
                'eth': AsyncEth
            },
            middlewares=[]  # geth_poa_middleware not supported yet
        )
        self.w3 = Web3(HTTPProvider(HTTP_URI))
        self.blockchain = blockchain
        self.status_init = False

    def init_contracts(self) -> []:
        summary = []
        private_keys = get_credentials(self.blockchain)
        contract_names = ['Migrations.sol', 'FileDigestOracle.sol', 'Factory.sol']

        print('Start deploy...')
        it = iter(private_keys)
        for pk_0, pk_1, pk_2 in zip(it, it, it):
            contract_addresses = []
            for contract in contract_names:
                pk = pk_2 if contract == contract_names[1] else pk_0

                if contract != contract_names[0]:
                    contract_addresses.append(self.__deploy_contract(contract, pk))

            summary.append({
                'contracts': {
                    contract_names[1]: contract_addresses[0],
                    contract_names[2]: contract_addresses[1]
                },
                'private_keys': [pk_0, pk_1, pk_2],
                'cloud_address': '0x0',
                'tx_upload_count': 0
            })

        filename = f'{self.blockchain}.json'
        filepath = os.path.join(os.getcwd(), CONFIG_DIR, filename)
        with open(filepath, 'w') as file:
            json.dump(summary, file, indent=4)
        print('Deploy completed.')
        print(f'Config file saved to {filepath}')
        self.status_init = True
        return summary

    def pks_to_addresses(self, pks: []) -> []:
        addresses = []
        for pk in pks:
            addresses.append(
                self.w3.eth.account.privateKeyToAccount(pk).address
            )
        return addresses if len(addresses) > 1 else addresses[0]

    def __deploy_contract(self, filename: str, pk: Address) -> ChecksumAddress:
        old_cwd = os.getcwd()
        filename_no_ext = filename.split('.')[0]
        key = f'{filename}:{filename_no_ext}'

        if Version(SOLC_VERSION) not in get_installed_solc_versions():
            install_solc(SOLC_VERSION)
        set_solc_version(SOLC_VERSION)

        os.chdir('../contracts')
        compiled_sol = compile_files(
            filename,
            output_values=['abi', 'bin']
        )

        os.chdir('../build/contracts')
        with open(f'{filename_no_ext}.json', 'w') as file:
            json.dump(compiled_sol[key], file, indent=4)

        # TODO: review
        if 'Factory' in filename:
            with open('CloudSLA.json', 'w') as file:
                json.dump(compiled_sol['CloudSLA.sol:CloudSLA'], file, indent=4)

        os.chdir(old_cwd)

        bytecode = compiled_sol[key]['bin']
        abi = compiled_sol[key]['abi']

        self.w3.eth.default_account = self.pks_to_addresses([pk])

        Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        tx = Contract.constructor().buildTransaction({
            'gasPrice': 0,
            'from': self.w3.eth.default_account,
            'nonce': self.w3.eth.get_transaction_count(self.w3.eth.default_account)
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=pk)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        contract = self.w3.eth.contract(
            address=tx_receipt.contractAddress,
            abi=abi
        )

        return contract.address
