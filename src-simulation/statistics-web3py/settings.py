from string import Template

SIMULATION_TIME = 600
TRANSIENT_VALUE = 50.

_RESULTS_PHASE_PATH = Template('../simulation-web3py/results/$phase')
TRANSIENT_PATH = _RESULTS_PHASE_PATH.substitute(phase='transient_200_15')
STEADY_STATE_PATH = _RESULTS_PHASE_PATH.substitute(phase='steady_state_600_5')

PLOT_DIR = 'plot'
RESULT_DIR = 'result'

functions = [
    'read',
    'upload',
    'delete',
    'file_check_undeleted_file',
    'read_deny_lost_file_check'
]

lambdas = [
    0.5,
    1.0,
    2.0
]

experiments = [
    'polygon_pos_4',
    'polygon_ibft_4',
    'besu_qbft_4',
    'besu_ibft_4',
    'besu_clique_4',
    'go-quorum_qbft_4',
    'go-quorum_ibft_4',
    'go-quorum_raft_4'
]
