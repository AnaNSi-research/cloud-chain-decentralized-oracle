import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

from settings import SIMULATION_TIME, PLOT_DIR, functions, lambdas
from utility import processing, truncate_length, extract_smooth_graph, exists_dir, join_paths

mpl.rc('figure', max_open_warning=0)


def response_time_blockchain(df: pd.DataFrame, operation) -> {}:
    data = processing(df, operation)
    return mu_confidence_interval(data)


def mu_confidence_interval(data: np.ndarray) -> {}:
    t = 1.64
    mu = np.mean(data)
    standard_deviation = np.std(data)
    M = data.shape[0]
    t_student = t * standard_deviation / np.sqrt(M)
    first_interval = mu - t_student
    second_interval = mu + t_student
    return {
        'mu': mu,
        't_student': t_student,
        'first_interval': first_interval,
        'second_interval': second_interval
    }


def number_users_system(df: pd.DataFrame) -> {}:
    throughput = processing(df, np.array, count_row=True)
    throughput /= SIMULATION_TIME
    #avg_response_time = processing(df, np.mean)
    users_number = throughput  # / avg_response_time
    return mu_confidence_interval(users_number)


def mean_error(df_all: pd.DataFrame, df_error: pd.DataFrame) -> {}:
    if df_error.shape[0] == 0:
        return {
            'mu': np.float64(0),
            't_student': np.float64(0)
        }

    errors = processing(df_error, np.array, count_row=True)
    totals = processing(df_all, np.array, count_row=True)
    percentage_error = errors / totals * 100
    return mu_confidence_interval(percentage_error)


def calculate_transient(df: pd.DataFrame) -> np.ndarray:
    num_repetition = len(df.groupby('num_run'))
    min_length = truncate_length(df, num_repetition)

    sums = np.zeros(min_length)
    for num_run in range(num_repetition):
        df_truncate = df[df['num_run'] == num_run]['time_fun'][:min_length]
        sums += df_truncate.to_numpy()

    means = np.zeros(min_length)
    for idx in range(min_length):
        means[idx] = sums[idx] / num_repetition

    smooth_data = extract_smooth_graph(means)
    return smooth_data


def plot_transient(df: pd.DataFrame, experiments: [], title: str, save: bool = False) -> None:
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_title(title, fontsize=24)

    df = df[df['exp'].isin(experiments)]

    for idx in range(df.shape[0]):
        ax.plot(df['transient'].iloc[idx][:60], label=df['exp'].iloc[idx])

    ax.legend(loc='upper left')
    plt.xlabel('Number of user')
    plt.ylabel('Time (s)')
    plt.yscale('log')
    plt.grid()

    if save:
        exists_dir(PLOT_DIR)
        figure_path = join_paths(PLOT_DIR, f'{title}.png')
        plt.savefig(figure_path)
    else:
        plt.show()


def bar_plot_metrics(df: pd.DataFrame, labels: [], title: str, column: str, save: bool = False) -> None:
    x = np.arange(len(labels))
    width = 0.1

    fig, ax = plt.subplots(figsize=(16, 10))

    rs = [x]
    for idx in range(1, df[column].unique().shape[0]):
        tmp = rs[idx - 1]
        rs.append(
            [val + width for val in tmp]
        )

    rects = []
    for idx, val in enumerate(df[column].unique()):
        metric_series = df[df[column] == val][labels].iloc[0]
        rects.append(
            ax.bar(rs[idx], metric_series, width, label=val)
        )

    ax.set_title(title, fontsize=24)
    ax.set_ylabel('Time (s)')

    y_max = df['max'].max() + 2.5
    ax.set_ylim(ymin=0, ymax=y_max)

    loc_ticks = [(val + (len(rects) / 2) * width) -
                 width / 2 for val in range(len(rects[0]))]
    upper_labels = [val.upper() for val in labels]
    ax.set_xticks(loc_ticks, upper_labels)
    ax.legend(loc='upper left')

    for rect in rects:
        ax.bar_label(rect, padding=3, rotation='vertical')

    fig.tight_layout()

    if save:
        exists_dir(PLOT_DIR)
        figure_path = join_paths(PLOT_DIR, f'{title}.png')
        plt.savefig(figure_path)
    else:
        plt.show()


def bar_plot_one_metric(df: pd.DataFrame, labels: [], metric: str, title: str, save: bool = False) -> None:
    x = np.arange(len(labels))
    width = 0.1

    fig, ax = plt.subplots(figsize=(16, 10))

    rs = [x]
    for idx in range(1, df['exp'].unique().shape[0]):
        tmp = rs[idx - 1]
        rs.append(
            [val + width for val in tmp]
        )

    rects = []
    for idx, val in enumerate(df['exp'].unique()):
        metric_series = pd.Series(df[df['exp'] == val][metric])
        rects.append(
            ax.bar(rs[idx], metric_series, width, label=val)
        )

    if metric == 'mean_error':
        y_label = '%'
        y_max = df[metric].max() + 2
    else:
        y_label = 'Number of user'
        y_max = df[metric].max() + 7.5

    ax.set_title(title, fontsize=24)
    ax.set_ylabel(y_label)
    ax.set_ylim(ymin=0, ymax=y_max)

    loc_ticks = [(val + (len(rects) / 2) * width) -
                 width / 2 for val in range(len(rects[0]))]
    ax.set_xticks(loc_ticks, labels)
    ax.legend(loc='upper left')

    for rect in rects:
        ax.bar_label(rect, padding=3, rotation='vertical')

    fig.tight_layout()

    if save:
        exists_dir(PLOT_DIR)
        figure_path = join_paths(PLOT_DIR, f'{title}.png')
        plt.savefig(figure_path)
    else:
        plt.show()


def new_plot(df_metrics: pd.DataFrame) -> None:
    fig, axs = plt.subplots(3, len(lambdas), sharex=True, sharey='row',
                            figsize=(7 * len(lambdas), 10), gridspec_kw={'height_ratios': [2.5, 0.7, 1]})
    labels = ['read', 'upload', 'delete', 'file_check', 'read_deny']

    for idl, l in enumerate(lambdas):
        df_filter_lambda = df_metrics[df_metrics['lambda'] == l]
        df_rounded_lambda = df_filter_lambda.round(1)
        df = df_rounded_lambda.sort_values(by=['exp'])

        metric = 'avg'
        metric2 = 'num_user'
        #title = 'prova'
        x = np.arange(len(labels))
        width = 0.1

        rs = [x]
        for idx in range(1, df['exp'].unique().shape[0]):
            tmp = rs[idx - 1]
            rs.append(
                [val + width for val in tmp]
            )

        rects = []
        rects2 = []
        for idx, val in enumerate(df['exp'].unique()):
            metric_series = pd.Series(df[df['exp'] == val][metric])
            throughput_series = pd.Series(df[df['exp'] == val][metric2])
            error_series = pd.Series(df[df['exp'] == val]['mean_error'])
            rects.append(
                axs[0][idl].bar(rs[idx], metric_series, width, label=val[0:-2])
            )
            rects2.append(
                axs[1][idl].bar(rs[idx], throughput_series,
                                width, label=val[0:-2])
            )
            axs[2][idl].bar(rs[idx], error_series, width, label=val[0:-2])

        for rect in rects:
            axs[0][idl].bar_label(rect, padding=4, rotation='vertical')
        for rect in rects2:
            axs[1][idl].bar_label(rect, padding=4, rotation='vertical')

        loc_ticks = [(val + (len(rects) / 2) * width) -
                     width / 2 for val in range(len(rects[0]))]
        axs[2][idl].set_xticks(loc_ticks, labels, rotation=45, ha="right")

    y_label = 'Avg Latency (sec)'
    y_label1 = 'Throughput (req/sec)'
    y_label2 = 'Errors (%)'
    y_max = df[metric].max() + 3
    y_max1 = df[metric2].max() + .4
    y_max2 = df['mean_error'].max() + 1

    #axs[0][0].set_title(title, fontsize=24)
    axs[0][0].set_ylabel(y_label)
    axs[1][0].set_ylabel(y_label1)
    axs[2][0].set_ylabel(y_label2)
    axs[0][0].set_ylim(ymin=0, ymax=y_max)
    axs[1][0].set_ylim(ymin=0, ymax=y_max1)
    axs[2][0].set_ylim(ymin=0, ymax=y_max2)
    axs[0][0].legend(loc='upper left')

    fig.tight_layout()

    plt.show()


def new_plot_transient(df: pd.DataFrame) -> None:
    _, ax = plt.subplots(figsize=(9, 7))

    exp_group = ['besu_ibft_4', 'go-quorum_ibft_4', 'polygon_ibft_4']
    #title = 'Transient with lambda'

    colors = list(mcolors.TABLEAU_COLORS)
    linestyles = ['-', '--', ':', '-.']
    flag = False
    patches = []
    for idl, l in enumerate(lambdas):
        df_filter = df[df['lambda'] == l]
        #title += f' - {l}'

        df_filter = df_filter[df_filter['exp'].isin(exp_group)]

        for idx in range(df_filter.shape[0]):
            ax.plot(df_filter['transient'].iloc[idx][:60],
                    linestyle=linestyles[idl % len(linestyles)], color=colors[idx])
            if not flag:
                patches.append(mpatches.Patch(
                    color=colors[idx], label=df_filter['exp'].iloc[idx]))
        flag = True
        patches.append(mlines.Line2D([], [], color='black',
                                     linestyle=linestyles[idl % len(
                                         linestyles)], label=f'lambda {l}'))

    #ax.set_title(title, fontsize=16)
    plt.legend(handles=patches)
    plt.xlabel('i-th operation request')
    plt.ylabel('Avg Latency (sec)')
    # plt.yscale('log')
    plt.grid()

    plt.show()
