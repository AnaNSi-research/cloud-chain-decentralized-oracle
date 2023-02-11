import asyncio

import argparse
import json
import os
import threading
from datetime import datetime

import numpy as np
import pandas as pd

from web3client import Web3Client
from contract_functions import ContractTest
from settings import DEBUG, RESULTS_CSV_DIR, DEPLOYED_CONTRACTS, CONFIG_DIR
from utility import range_limited_val, init_simulation, get_contracts_config, exists_mkdir


def between_callback(process_count: int, fn: str):
    global df
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    func_to_run = fn + '()'
    df_to_append = loop.run_until_complete(get_time(func_to_run, process_count))
    loop.close()
    df = pd.concat([df, df_to_append], ignore_index=True)


async def get_time(func_to_run: str, process_count: int) -> pd.DataFrame:
    # Flag statuses
    function_status = False
    # Values to store
    cloud_address = 'NaN'
    start_fun, end_fun = datetime.now(), datetime.now()

    try:
        if 'cloud_sla_creation_activation' in func_to_run:
            start_fun = datetime.now()
            cloud_address, function_status = await eval(func_to_run)
            end_fun = datetime.now()
        else:
            start_fun = datetime.now()
            function_status = await eval(func_to_run)
            end_fun = datetime.now()
    except ValueError as v:
        print(f'{type(v)} [get_time#{process_count}]: {v}')
        function_status = False
        end_fun = datetime.now()
    finally:
        duration_fun = end_fun - start_fun

        return pd.DataFrame({
            'id': [process_count],
            'start_fun': [(start_fun - zero_time).total_seconds()],
            'end_fun': [(end_fun - zero_time).total_seconds()],
            'time_fun': [duration_fun.total_seconds()],
            'address': [cloud_address],
            'status': function_status,
            'lambda': args.lambda_p,
            'num_run': args.num_run
        })


async def main():
    print('Start init phase...')
    init = await init_simulation(contracts, (args.lambda_p + 0.1) * args.time, args.function, client.status_init)
    if not init:
        print('Error with init phase.')
        exit(1)
    print('Init phase completed.')

    print('Start simulation...')

    start = (datetime.now() - zero_time).total_seconds()
    actual = (datetime.now() - zero_time).total_seconds()
    idx = 0
    jobs = []
    while actual < start + args.time:
        thread = threading.Thread(
            target=between_callback,
            args=[idx, f'contracts[{idx % DEPLOYED_CONTRACTS}].{args.function}']
        )
        jobs.append(thread)

        actual = (datetime.now() - zero_time).total_seconds()
        rand = np.random.exponential(1 / args.lambda_p)
        await asyncio.sleep(rand)
        jobs[idx].start()
        idx += 1

    for j in jobs:
        j.join()

    if DEBUG:
        print(df)
        print(f"Status column:\n{df[['id', 'status']]}")
        print(f"Rows with status True: {len(df.loc[df['status']])}")
    print('Simulation completed.')

    update_summary = get_contracts_config(args.blockchain, msg=False)
    for idx, c in enumerate(contracts):
        update_summary[idx]['cloud_address'] = c.cloud_address
        update_summary[idx]['tx_upload_count'] = c.tx_upload_count

    config = f'{args.blockchain}.json'
    filepath = os.path.join(os.getcwd(), CONFIG_DIR, config)
    with open(filepath, 'w') as file:
        json.dump(update_summary, file, indent=4)

    if args.save:
        path = os.getcwd()
        results_dir = os.path.join(path, RESULTS_CSV_DIR)
        test_dir = os.path.join(results_dir, args.experiment)
        out_dir = os.path.join(test_dir, args.function)
        exists_mkdir([results_dir, test_dir, out_dir])
        out_file = f'simulation{args.num_run}_{args.lambda_p}_{args.function}_{args.experiment}.csv'
        results_path = os.path.join(out_dir, out_file)
        df.to_csv(results_path, index=False, encoding='utf-8')
        print(f'Output file saved in {results_path}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script written using web3py to test different blockchains.',
        usage='%(prog)s blockchain function [-t TIME] [-l LAMBDA] [-d] [-s [-n NUM_RUN] [-e] EXPERIMENT]'
    )
    parser.add_argument(
        'blockchain', default='none', type=str,
        choices=['polygon', 'besu', 'go-quorum'],
        help='the name of the blockchain'
    )
    parser.add_argument(
        'function', default='none', type=str,
        choices=[
            'cloud_sla_creation_activation',
            'upload',
            'read',
            'delete',
            'file_check_undeleted_file',
            'another_file_upload',
            'read_deny_lost_file_check',
            'another_file_upload_read',
            'corrupted_file_check'
        ],
        help='the name of the function to stress'
    )
    parser.add_argument(
        '-t', '--time', default=10,
        type=range_limited_val,
        help='the number of seconds to run'
    )
    parser.add_argument(
        '-l', '--lambda_p', default=.5,
        type=float, choices=[2, 1, .5, .2, .1],
        help='the lambda parameter for interarrival time Poisson'
    )
    parser.add_argument(
        '-d', '--deploy', default=False,
        action='store_true',
        help='deploy contracts to blockchain'
    )
    parser.add_argument(
        '-s', '--save', default=False,
        action='store_true',
        help='save csv file as output'
    )
    parser.add_argument(
        '-n', '--num_run', default=-1,
        type=range_limited_val,
        help='the id number for the output file'
    )
    parser.add_argument(
        '-e', '--experiment', default='none', type=str,
        choices=[
            'polygon_ibft_4',
            'polygon_pos_4',
            'besu_qbft_4',
            'besu_ibft_4',
            'besu_clique_4',
            'go-quorum_qbft_4',
            'go-quorum_ibft_4',
            'go-quorum_raft_4'
        ],
        help='the output folder of the experiment'
    )

    args = parser.parse_args()
    if args.save:
        if args.num_run == -1:
            parser.error("specify the id number for the output file")
        if args.experiment == 'none':
            parser.error("specify the experiment folder for the output file")

    zero_time = datetime.now()
    df = pd.DataFrame()
    client = Web3Client(args.blockchain)

    config_dir = os.path.join(os.getcwd(), CONFIG_DIR)
    if not os.path.exists(config_dir):
        print("Config dir doesn't exist...")
        os.mkdir(config_dir)
        print('Config dir created.')
    filename = f'{args.blockchain}.json'
    config_file = os.path.join(config_dir, filename)
    if args.deploy:
        contracts_summary = client.init_contracts()
    else:
        if not os.path.exists(config_file):
            print(f"Config file doesn't exist...")
            contracts_summary = client.init_contracts()
        else:
            contracts_summary = get_contracts_config(args.blockchain)

    contracts = []
    for i in range(DEPLOYED_CONTRACTS):
        index = i % DEPLOYED_CONTRACTS
        contracts.append(
            ContractTest(
                client.w3,
                client.w3_async,
                client.pks_to_addresses(contracts_summary[index]['private_keys']),
                contracts_summary[index]['private_keys'],
                contracts_summary[index]['contracts'],
                contracts_summary[index]['cloud_address'],
                contracts_summary[index]['tx_upload_count']
            )
        )

    exit(asyncio.run(main()))
