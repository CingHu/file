from oslo.config.cfg import IntOpt, StrOpt


DEFAULT_OPTS = [
    StrOpt(
        'clb_state_path',
        default='$state_path/clb',
        help="Location to store config and state files"),
]

ROOT_HELPER_OPTS = [
    StrOpt(
        'root_helper',
        default='sudo neutron-rootwrap /etc/neutron/rootwrap.conf',
        help="Root helper application"),
]


AGENT_OPTS = [
    IntOpt(
        'periodic_interval',
        default=10,
        help="Seconds between periodic task runs"),
    StrOpt(
        'interface_driver',
        default='neutron.agent.linux.interface.OVSInterfaceDriver',
        help="The driver used to manage the virtual interface"),

    IntOpt(
        'report_interval',
        default=4,
        help="Seconds between nodes reporting state to server; "
             "should be less than agent_down_time, best if it "
             "is half or less than agent_down_time."),
    StrOpt(
        'driver',
        default='neutron.clb.agent.drivers.haproxy.driver.HaproxyDriver',
        help="Driver used to manage load balancing devices"),
]


HAPROXY_OPTS = [
    StrOpt(
        'user',
        default='neutron',
        help="The haproxy user"),
    StrOpt(
        'group',
        default='neutron',
        help="The haproxy group"),
    IntOpt(
        'send_gratuitous_arp',
        default=3,
        help="Count of arp anouncment after routes changing"),
    StrOpt(
        'haproxy_bin',
        default='/opt/haproxy/usr/local/sbin/haproxy',
        help="Path of Haproxy binary"),
]


def register_opts(conf):
    conf.register_opts(DEFAULT_OPTS)
    conf.register_opts(ROOT_HELPER_OPTS)
    conf.register_opts(ROOT_HELPER_OPTS, 'AGENT')
    conf.register_opts(AGENT_OPTS, 'AGENT')
    conf.register_opts(HAPROXY_OPTS, 'Haproxy')
    


