#coding: utf-8
import os
import itertools
from six import moves
from oslo.config.cfg import CONF
from neutron.clb.common import constants
from neutron.clb.agent.drivers.haproxy import utils


FRONTEND_PROTOCOL_MAP = {
    constants.PROTOCOL_TCP: 'tcp',
    constants.PROTOCOL_HTTP: 'http',
    constants.PROTOCOL_HTTPS: 'http',
}


BACKEND_PROTOCOL_MAP = {
    constants.PROTOCOL_TCP: 'tcp',
    constants.PROTOCOL_HTTP: 'http',
    constants.PROTOCOL_HTTPS: 'http',
}


BALANCE_MAP = {
    constants.LB_METHOD_ROUND_ROBIN: 'roundrobin',
    constants.LB_METHOD_LEAST_CONNECTIONS: 'leastconn',
    constants.LB_METHOD_SOURCE_IP: 'source'
}


def _get_pem_file_path(lb_id, listener):
    if listener.get('certificate_id'):
        lb_dir = utils.get_load_balancer_dir(lb_id)
        return os.path.join(lb_dir, '%s.pem' % listener['certificate_id'])
    else:
        return None


def get_haproxy_config_text(lb):
    lines = []
    sock_file = utils.get_sock_file_path(lb['id'])
    lines.extend(_build_global_lines(lb,
                                     CONF.Haproxy.user,
                                     CONF.Haproxy.group,
                                     sock_file))
    lines.extend(_build_default_lines())
    for listener in lb['listeners']:
        pem_file_path = _get_pem_file_path(lb['id'], listener)
        lines.extend(_build_frontend_lines(listener,
                                           pem_file_path=pem_file_path))
        lines.extend(_build_backend_lines(listener))
    return '\n'.join(lines)


def _build_global_lines(load_balancer, user, group, sock_path=None):
    lines = ['daemon']
    lines.append('user %s' % user)
    lines.append('group %s' % group)
    lines.append('log /dev/log local0')
    lines.append('log /dev/log local1 notice')

    if load_balancer['maxconn'] > 0:
        lines.append('maxconn %(maxconn)d' % load_balancer)

    if sock_path:
        line = 'stats socket %s mode 0666 level user' % sock_path
        lines.append(line)
    
    return itertools.chain(
        ['global'],
        ('\t' + line for line in lines)
    )


def _build_default_lines():
    lines = [
        'log global',
        'retries 3',
        'option redispatch',
        'timeout connect 5000',
        'timeout client 50000',
        'timeout server 50000',
    ]

    return itertools.chain(
        ['defaults'],
        ('\t' + line for line in lines)
    )


def _build_frontend_lines(listener, pem_file_path=None):
    protocol = listener['server_protocol']

    lines = []

    if listener['listen_addr'] == '0.0.0.0':
        bind_line = 'bind :%(listen_port)d' % listener
    else:
        bind_line = 'bind %(listen_addr)s:%(listen_port)d' % listener

    # Fixme: what if there is not a pem_file provided
    if protocol == constants.PROTOCOL_HTTPS:
        bind_line = '%s ssl crt %s' % (bind_line, pem_file_path)
    lines.append(bind_line)

    lines.append('mode %s' % FRONTEND_PROTOCOL_MAP[protocol])
    lines.append('default_backend %(id)s' % listener)

    if listener['server_maxconn'] > 0:
        lines.append('maxconn %(server_maxconn)s' % listener)

    if protocol == constants.PROTOCOL_TCP:
        lines.append('option tcplog')
    elif protocol == constants.PROTOCOL_HTTP:
        lines.append('option httplog')
        lines.append('option forwardfor')
    elif protocol == constants.PROTOCOL_HTTPS:
        lines.append('option httplog')
        lines.append('option forwardfor')

    return itertools.chain(
        ['frontend %(id)s' % listener],
        ('\t' + line for line in lines)
    )


def _build_backend_lines(listener):
    protocol = listener['server_protocol']
    method = listener['load_balance_method']

    lines = [
        'mode %s' % BACKEND_PROTOCOL_MAP[protocol],
        'balance %s' % BALANCE_MAP.get(method, 'roundrobin')
    ]

    if protocol == constants.PROTOCOL_HTTP:
        lines.append('option http-server-close')
    elif protocol == constants.PROTOCOL_HTTPS:
        lines.append('reqadd X-Forwarded-Proto:\ https')
        lines.append('option http-server-close')

    # add health check (if available)
    server_line_addon, hc_lines = _build_health_check_lines(listener)
    lines.extend(hc_lines)

    # add session persistence (if available)
    sp_lines = _build_session_persistence_lines(listener)
    lines.extend(sp_lines)

    # add backends
    lines.extend(_build_server_lines(listener, server_line_addon))

    return itertools.chain(
        ['backend %(id)s' % listener],
        ('\t' + line for line in lines)
    )


def _build_server_lines(listener, server_line_addon):
    lines = []

    enabled_backends = [backend for backend in listener['backends']
                        if backend['enabled']]

    for idx, backend in enumerate(enabled_backends):
        server_line = ('server %(id)s %(listen_addr)s:%(listen_port)s '
                       'weight %(weight)s' % backend)
        server_line += server_line_addon

        if _has_http_cookie_persistence(listener):
            server_line += ' cookie %d' % idx
        lines.append(server_line)

    return lines


def _build_health_check_lines(listener):
    server_line_addon = ''
    lines = []

    if 'health_check' not in listener:
        return server_line_addon, lines

    health_check = listener['health_check']
    if not health_check['enabled']:
        return server_line_addon, lines

    check_addon = ' check inter %(delay)ds rise %(rise)d fall %(fall)d'
    server_line_addon = check_addon % health_check

    lines.append('timeout check %(timeout)ds' % health_check)

    hc_type_http_and_https = (constants.HEALTH_CHECK_HTTP,
                              constants.HEALTH_CHECK_HTTPS)
    if health_check['type'] in hc_type_http_and_https:
        lines.append(
            'option httpchk %(http_method)s %(http_url_path)s' % health_check
        )
        lines.append(_build_expect_rstatus_line(health_check))

    return server_line_addon, lines


def _build_session_persistence_lines(listener):
    sp = listener.get('session_persistence')
    if not sp: # or not sp['enabled']:
        return []

    lines = []
    if sp['type'] == constants.SP_SOURCE_IP:
        lines.append('stick-table type ip size 10k')
        lines.append('stick on src')
    elif sp['type'] == constants.SP_HTTP_COOKIE and listener.get('backends'):
        lines.append('cookie PORXYSRV insert indirect nocache')
    elif sp['type'] == constants.SP_APP_COOKIE and sp.get('cookie_name'):
        lines.append('appsession %(cookie_name)s len 52 timeout 3h' % sp)

    return lines


def _has_http_cookie_persistence(listener):
    if 'session_persistence' in listener:
        sp_type = listener['session_persistence']['type']
        if sp_type == constants.SP_HTTP_COOKIE:
            return True
    return False


def _build_expect_rstatus_line(health_check):
    expect_rstatus = _expand_http_expected_codes(
        health_check['http_expected_codes']
    )
    return 'http-check expect rstatus %s' % '|'.join(expect_rstatus)


def _expand_http_expected_codes(codes):
    """Expand the expected code string in set of codes.

    200-204 -> 200, 201, 202, 204
    200, 203 -> 200, 203
    """

    retval = set()
    for code in codes.replace(',', ' ').split(' '):
        code = code.strip()

        if not code:
            continue
        elif '-' in code:
            low, hi = code.split('-')[:2]
            retval.update(str(i) for i in moves.xrange(int(low), int(hi) + 1))
        else:
            retval.add(code)
    return retval
