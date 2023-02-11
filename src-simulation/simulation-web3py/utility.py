import json
import os
from argparse import ArgumentTypeError

from eth_typing import Address
from web3.contract import Contract

from settings import MIN_VAL, MAX_VAL, DEPLOYED_CONTRACTS, CONFIG_DIR


async def init_simulation(contracts: [], factor: float, fn: str, status_init: bool) -> bool:
    statuses = [True]
    try:
        if status_init:
            for c in contracts:
                # Use different cloud_addresses for each contract instance
                cloud_address, cloud_status_ok = await c.cloud_sla_creation_activation()
                c.set_cloud_sla_address(cloud_address)
                statuses.append(cloud_status_ok)
                if fn == 'read' or fn == 'read_deny_lost_file_check' or fn == 'file_check_undeleted_file':
                    statuses.append(await c.upload())
                if fn == 'file_check_undeleted_file':
                    statuses.append(await c.read())
                if fn == 'corrupted_file_check':
                    statuses.append(await c.another_file_upload_read())
                if fn == 'delete':
                    for _ in range(round(factor / DEPLOYED_CONTRACTS) + 1):
                        statuses.append(await c.upload())
        else:
            for c in contracts:
                if fn == 'delete':
                    if c.tx_upload_count < round(factor / DEPLOYED_CONTRACTS) + 1:
                        for _ in range(abs(c.tx_upload_count - (round(factor / DEPLOYED_CONTRACTS) + 1))):
                            statuses.append(await c.upload())

    except ValueError as v:
        print(f'{type(v)} [init_sim]: {v}')
    else:
        return check_statuses(statuses)


def get_credentials(blockchain: str) -> tuple:
    if blockchain == 'polygon':
        from settings import (
            polygon_private_keys
        )
        return polygon_private_keys
    from settings import (
        quorum_private_keys
    )
    return quorum_private_keys


def get_contract(w3, address: Address, compiled_contract_path: str) -> Contract:
    def get_abi(path: str) -> list:
        with open(path) as file:
            contract_json = json.load(file)
            contract_abi = contract_json['abi']
        return contract_abi

    abi = get_abi(compiled_contract_path)
    contract = w3.eth.contract(address=address, abi=abi)

    return contract


def check_statuses(statuses: []) -> bool:
    for idx in range(len(statuses)):
        if statuses[idx] == 0:
            return False
    return True


def exists_mkdir(paths: []):
    for path in paths:
        if not os.path.exists(path):
            os.mkdir(path)


def get_contracts_config(blockchain: str, msg: bool = True):
    if msg:
        print('Retrieve config file...')
    filename = f'{blockchain}.json'
    filepath = os.path.join(os.getcwd(), CONFIG_DIR, filename)
    with open(filepath) as file:
        contracts_summary = json.loads(file.read())
    if msg:
        print(f'Config file retrieved at {filepath}.')
    return contracts_summary


def range_limited_val(arg: str) -> int:
    """
    Type function for argparse - int within some predefined bounds.
    """
    try:
        s = int(arg)
    except ValueError:
        raise ArgumentTypeError("must be a int number")
    if s < MIN_VAL or s > MAX_VAL:
        raise ArgumentTypeError(f"argument must be > {str(MIN_VAL)} and < {str(MAX_VAL)}")
    return s
