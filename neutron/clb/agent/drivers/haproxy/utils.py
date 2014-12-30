import os
import shutil
from oslo.config.cfg import CONF
from neutron.clb.common import constants


def get_namespace(lb_id):
    """Get network namespace for load balancer.
    :param lb_id: (uuid) load balancer id
    :return netns: (str) network namespace of load balancer
    """
    return constants.NS_PREFIX + lb_id


def get_state_dir():
    return os.path.abspath(os.path.normpath(CONF.clb_state_path))


def get_load_balancer_dir(lb_id):
    return os.path.join(get_state_dir(), lb_id)


def get_sock_file_path(lb_id):
    return os.path.join(get_load_balancer_dir(lb_id), 'haproxy.sock')


def get_pid_file_path(lb_id):
    return os.path.join(get_load_balancer_dir(lb_id), 'haproxy.pid')


def get_cfg_file_path(lb_id):
    return os.path.join(get_load_balancer_dir(lb_id), 'haproxy.cfg')


def ensure_state_dir():
    state_dir_path = get_state_dir()
    if not os.path.isdir(state_dir_path):
        os.makedirs(state_dir_path, 0o755)


def ensure_load_balancer_dir(lb_id):
    lb_dir_path = get_load_balancer_dir(lb_id)
    if not os.path.isdir(lb_dir_path):
        os.makedirs(lb_dir_path, 0o755)


def remove_load_balancer_dir(lb_id):
    lb_dir_path = get_load_balancer_dir(lb_id)
    if os.path.isdir(lb_dir_path):
        shutil.rmtree(lb_dir_path)


def get_pid(pid_file):
    """Get process PID from a PID file.
    :param pid_file: (str) path of PID file
    :return: pid: (str) process PID
    :raise IOError
    """
    with open(pid_file, 'r') as f:
        for line in f:
            if line.strip():
                return line.strip()

