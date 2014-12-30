#coding: utf-8
import os
import socket
from neutron.openstack.common import log
from neutron.clb.common import constants
from neutron.clb.agent.drivers.haproxy import utils


STATS_MAP = {
    constants.STATS_ACTIVE_CONNECTIONS: 'scur',
    constants.STATS_MAX_CONNECTIONS: 'smax',
    constants.STATS_CURRENT_SESSIONS: 'scur',
    constants.STATS_MAX_SESSIONS: 'smax',
    constants.STATS_TOTAL_CONNECTIONS: 'stot',
    constants.STATS_TOTAL_SESSIONS: 'stot',
    constants.STATS_IN_BYTES: 'bin',
    constants.STATS_OUT_BYTES: 'bout',
    constants.STATS_CONNECTION_ERRORS: 'econ',
    constants.STATS_RESPONSE_ERRORS: 'eresp'
}


LOG = log.getLogger(__name__)


TYPE_BACKEND_REQUEST = 2
TYPE_SERVER_REQUEST = 4

TYPE_BACKEND_RESPONSE = '1'
TYPE_SERVER_RESPONSE = '2'


def collect_lb_stats(lb_id):
    """Collect load balancer Haproxy process run time information.
    For OpenStack Havana we only return backend information.
    :param lb_id: (uuid) load balancer id
    :return backend_stats: (dict) backend information
    """
    backend_stats = {}
    sock_file = utils.get_sock_file_path(lb_id)

    if os.path.exists(sock_file):
        try:
            raw_stats = _get_raw_stats_from_socket(sock_file)
            try:
                parsed_stats = _parse_stats(raw_stats)
                listener_stats = _get_backend_stats(parsed_stats)
                backend_stats = _get_servers_stats(parsed_stats)
            except Exception as e:
                msg = "Parse statistic data failed: %s (%s)"
                LOG.warn(msg % (e, raw_stats))
        except socket.error as e:
            # this may be caused by a uncleaned socket, log in debug level
            msg = "Get statistic data from socket failed: %s (%s)"
            LOG.debug(msg % (e, sock_file))

    return backend_stats


def _get_raw_stats_from_socket(sock_file):
    """Get raw statistic data from Haproxy socket.
    :param sock_file: unix socket path
    """
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(sock_file)

    entity_type = TYPE_BACKEND_REQUEST | TYPE_SERVER_REQUEST
    s.send('show stat -1 %s -1\n' % entity_type)

    raw_stats = ''
    chunk_size = 1024
    while True:
        chunk = s.recv(chunk_size)
        raw_stats += chunk
        if len(chunk) < chunk_size:
            break

    return raw_stats


def _parse_stats(raw_stats):
    stat_lines = raw_stats.splitlines()

    if len(stat_lines) < 2:
        return []

    stat_names = [name.strip('# ') for name in stat_lines[0].split(',')]

    res_stats = []
    for raw_values in stat_lines[1:]:
        if raw_values:
            stat_values = [value.strip() for value in raw_values.split(',')]
            res_stats.append(dict(zip(stat_names, stat_values)))

    return res_stats


def _get_backend_stats(parsed_stats):
    for stats in parsed_stats:
        if stats.get('type') == TYPE_BACKEND_RESPONSE:
            unified_stats = dict(
                (k, stats.get(v, '')) for k, v in STATS_MAP.items()
            )
            return unified_stats
    return {}


def _get_servers_stats(parsed_stats):
    """Get server statistic data for parsed Haproxy socket repsonse text.
    :param parsed_stats: parsed Haproxy socket repsonse data (dict)
    :return server_stats: server_name => server_data (dict)
    """
    server_stats = {}
    for stats in parsed_stats:
        if stats.get('type') == TYPE_SERVER_RESPONSE:
            server_stats[stats['svname']] = {
                constants.STATS_STATUS: (constants.HEALTH_DOWN
                                         if stats['status'] == 'DOWN'
                                         else constants.HEALTH_ACTIVE),
                constants.STATS_HEALTH: stats['check_status'],
                constants.STATS_FAILED_CHECKS: stats['chkfail']
            }
    return server_stats


