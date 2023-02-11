import os
from string import Template

import numpy as np
import pandas as pd


def exists_dir(path: str):
    if not os.path.exists(path):
        os.mkdir(path)


def join_paths(first_path: str, second_path: str):
    return os.path.join(first_path, second_path)


def phase_path(transient: bool) -> str:
    if transient:
        from settings import TRANSIENT_PATH
        return TRANSIENT_PATH
    from settings import STEADY_STATE_PATH
    return STEADY_STATE_PATH


def experiment_path(experiment: str, path: str) -> ():
    if experiment == 'none':
        exp_paths = []
        for exp in os.listdir(path):
            dir_path = f'{path}/{exp}'
            if os.path.isdir(dir_path):
                exp_paths.append(
                    Template(f'{dir_path}/$fn')
                )
        return True, exp_paths

    single_exp = f'{path}/{experiment}'
    if os.path.isdir(single_exp):
        return True, [Template(f'{single_exp}/$fn')]
    return False, []


def read_csv(path: Template, functions: []) -> {}:
    dict_df = {}
    for fn in functions:
        dict_df[fn] = []
        function_path = path.substitute(fn=fn)
        for filename in os.listdir(function_path):
            dict_df[fn].append(
                pd.read_csv(os.path.join(function_path, filename))
            )
    return dict_df


def extract_data_function(dict_df: {}, fn: str) -> pd.DataFrame:
    df = pd.concat(dict_df[fn], ignore_index=True)
    return df


def filter_lambda_status(df: pd.DataFrame, lambda_p: float, status: bool = True) -> pd.DataFrame:
    return df[(df['lambda'] == lambda_p) & (df['status'] == status)]


def filter_fn_lambda(df: pd.DataFrame, fn: str, lambda_p: float) -> pd.DataFrame:
    return df[(df['fn'] == fn) & (df['lambda'] == lambda_p)]


def filter_transient_time(df: pd.DataFrame, time: np.float64) -> pd.DataFrame:
    return df[df['start_fun'] > time]


def processing(df: pd.DataFrame, operation, count_row: bool = False) -> np.ndarray:
    data = np.array([])
    num_repetition = range(5) if count_row else df['num_run'].unique()
    for num_run in num_repetition:
        df_tmp = df[df['num_run'] == num_run]['time_fun']
        data = np.append(
            data,
            np.array(operation(df_tmp.shape[0] if count_row else df_tmp))
        )

    return data


def truncate_length(df: pd.DataFrame, num_repetition: int) -> int:
    lengths = np.array([], dtype=int)
    for num_run in range(num_repetition):
        lengths = np.append(
            lengths,
            df[df['num_run'] == num_run].shape[0]
        )
    return np.min(lengths)


def extract_smooth_graph(mu: np.ndarray, k: int = 10) -> np.ndarray:
    tmp = mu
    for idx in range(len(mu) - (k + 1)):
        tmp[idx] = short_term_fluctuations(idx, k, mu)
    return tmp


def short_term_fluctuations(n: int, k: int, mu: np.ndarray) -> float:
    value = .0

    if n >= k + 1:
        iterator = range(-k, k)
        divisor = (2 * k + 1)
    else:
        iterator = range(-(n - 1), (n - 1))
        divisor = (2 * n - 1)

    for idx in iterator:
        value += mu[n + idx]

    value /= divisor
    return value
