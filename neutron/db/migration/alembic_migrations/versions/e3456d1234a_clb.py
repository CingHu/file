"""Chinac load balance plugin models"""

revision = 'e3456d1234a'
down_revision = '31fbcaef8a26'

from sqlalchemy import Column, String, Boolean, Integer, BigInteger, DateTime
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint
from alembic import op


def upgrade():
    op.create_table(
        'clb_load_balancers',
        Column('id',          String(36),  nullable=False),
        Column('tenant_id',   String(255), nullable=False),
        Column('state',       String(32),  nullable=False),
        Column('task_state',  String(64),  nullable=False),
        Column('provider',    String(32),  nullable=False),
        Column('maxconn',     Integer,     nullable=False),
        Column('name',        String(128), nullable=True),
        Column('description', String(255), nullable=True),
        PrimaryKeyConstraint('id')
    )

    op.create_table(
        'clb_load_balancer_agent_bindings',
        Column('load_balancer_id', String(36), nullable=False),
        Column('agent_id',         String(36), nullable=False),
        ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['load_balancer_id'], ['clb_load_balancers.id'],
                             ondelete='CASCADE'),
        PrimaryKeyConstraint('load_balancer_id')
    )

    op.create_table(
        'clb_interfaces',
        Column('id',               String(36),  nullable=False),
        Column('tenant_id',        String(255), nullable=False),
        Column('state',            String(32),  nullable=False),
        Column('task_state',       String(64),  nullable=False),
        Column('enabled',          Boolean(),   nullable=False),
        Column('is_public',        Boolean(),   nullable=False),
        Column('load_balancer_id', String(36),  nullable=False),
        Column('port_id',          String(36),  nullable=True),
        Column('inbound_limit',    Integer,     nullable=True),
        Column('outbound_limit',   Integer,     nullable=True),
        PrimaryKeyConstraint('id'),
        ForeignKeyConstraint(['load_balancer_id'], ['clb_load_balancers.id']),
        ForeignKeyConstraint(['port_id'], ['ports.id'])
    )

    op.create_table(
        'clb_listeners',
        Column('id',               String(36),     nullable=False),
        Column('tenant_id',        String(255),    nullable=False),
        Column('state',            String(32),     nullable=False),
        Column('task_state',       String(64),     nullable=False),
        Column('enabled',          Boolean(),      nullable=False),
        Column('server_protocol',  String(64),     nullable=False),
        Column('server_maxconn',   Integer,        nullable=False),
        Column('listen_addr',      String(64),     nullable=False),
        Column('listen_port',      Integer,        nullable=False),
        Column('load_balancer_id', String(36),     nullable=False),
        Column('load_balance_method',  String(64), nullable=False),
        Column('name',             String(128),    nullable=True),
        Column('description',      String(255),    nullable=True),
        Column('certificate_id',   String(36),     nullable=True),
        PrimaryKeyConstraint('id'),
        ForeignKeyConstraint(['load_balancer_id'], ['clb_load_balancers.id'])
    )

    op.create_table(
        'clb_session_persistences',
        Column('listener_id',      String(36),     nullable=False),
        Column('type',             String(64),     nullable=False),
        Column('cookie_name',      String(1024),   nullable=True),
        PrimaryKeyConstraint('listener_id'),
        ForeignKeyConstraint(['listener_id'], ['clb_listeners.id'])
    )

    op.create_table(
        'clb_health_checks',
        Column('listener_id',      String(36),     nullable=False),
        Column('enabled',          Boolean(),      nullable=False),
        Column('type',             String(32),     nullable=False),
        Column('timeout',          Integer,        nullable=False),
        Column('delay',            Integer,        nullable=False),
        Column('fall',             Integer,        nullable=False),
        Column('rise',             Integer,        nullable=False),
        Column('http_method',      String(16),     nullable=True),
        Column('http_url_path',    String(255),    nullable=True),
        Column('http_expected_codes',  String(255),nullable=True),
        PrimaryKeyConstraint('listener_id'),
        ForeignKeyConstraint(['listener_id'], ['clb_listeners.id'])
    )

    op.create_table(
        'clb_backends',
        Column('id',               String(36),     nullable=False),
        Column('tenant_id',        String(255),    nullable=False),
        Column('enabled',          Boolean(),      nullable=False),
        Column('listen_addr',      String(64),     nullable=False),
        Column('listen_port',      Integer,        nullable=False),
        Column('weight',           Integer,        nullable=False),
        Column('health_state',     String(36),     nullable=False),
        Column('name',             String(128),    nullable=True),
        Column('description',      String(255),    nullable=True),
        Column('listener_id',      String(36),     nullable=True),
        Column('updated_at',       DateTime,       nullable=False),
        PrimaryKeyConstraint('id'),
        ForeignKeyConstraint(['listener_id'], ['clb_listeners.id'])
    )

    op.create_table(
        'clb_listener_statistics',
        Column('listener_id',      String(36),     nullable=False),
        Column('bytes_in',         BigInteger,     nullable=False),
        Column('bytes_out',        BigInteger,     nullable=False),
        Column('active_connections',   BigInteger, nullable=False),
        Column('total_connections',    BigInteger, nullable=False),
        PrimaryKeyConstraint('listener_id'),
        ForeignKeyConstraint(['listener_id'], ['clb_listeners.id'])
    )

    op.create_table(
        'clb_certificates',
        Column('id',               String(36),     nullable=False),
        Column('tenant_id',        String(255),    nullable=False),
        Column('load_balancer_id', String(36),     nullable=False),
        Column('certificate',      String(2048),   nullable=False),
        Column('key',              String(2048),   nullable=False),
        Column('name',             String(128),    nullable=True),
        Column('description',      String(255),    nullable=True),
        PrimaryKeyConstraint('id'),
        ForeignKeyConstraint(['load_balancer_id'], ['clb_load_balancers.id'])
    )


def downgrade(active_plugins=None, options=None):
    op.drop_table('clb_load_balancers')
    op.drop_table('clb_load_balancer_agent_bindings')
    op.drop_table('clb_listeners')
    op.drop_table('clb_interfaces')
    op.drop_table('clb_session_persistences')
    op.drop_table('clb_health_checks')
    op.drop_table('clb_backends')
    op.drop_table('clb_listener_statistics')
    op.drop_table('clb_certificates')
