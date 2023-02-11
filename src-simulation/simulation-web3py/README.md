# simulation-web3py

We used the [web3py](https://web3py.readthedocs.io/en/stable/) library to interact with the contract [*CloudSLA.sol*](https://github.com/cotus997/cloud-chain-simulation/blob/main/contracts/CloudSLA.sol). In particular we used asynchronous call to test the following contract functions:

- `upload`
- `read`
- `delete`
- `read_deny_lost_file_check`
- `file_check_undeleted_file`

In order to make a good simulation we also used threads.

## Setup

To execute the script, Python must be installed([download](https://www.python.org/downloads/)), and some external libraries must be downloaded and installed using the pip (or pip3) package manager:

```bash
pip install -r requirements.txt
```

## Usage

```python
python main.py blockchain function [-t TIME] [-l LAMBDA] [-d] [-s [-n NUM_RUN] [-e EXPERIMENT]]
```

To know the allowed parameters use

```python
python main.py -h
```

## Collecting data simulation

The [*run_simulation.sh*](https://github.com/cotus997/cloud-chain-simulation/blob/main/simulation-web3py/run_simulation.sh) script helped us to automate the data collection. Also in this script there aren't any handle of typing errror.
