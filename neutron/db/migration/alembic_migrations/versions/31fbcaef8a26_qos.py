# Copyright 2014 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Add QoS db models

Revision ID: 31fbcaef8a26
Revises: 3f262f6b0251
Create Date: 2014-12-8 10:53:29.669259

"""

# revision identifiers, used by Alembic.
revision = '31fbcaef8a26'
down_revision = '3f262f6b0251'


from neutron.common import constants
from neutron.db import migration

from alembic import op
import sqlalchemy as sa

qos_types = sa.Enum(constants.TYPE_QOS_DSCP,
                   constants.TYPE_QOS_RATELIMIT,
                   name='qos_types')
            

def upgrade(active_plugins=None, options=None):

    if not migration.schema_has_table("qoses"):
        op.create_table(
            'qoses',
            sa.Column('tenant_id', sa.String(length=255), nullable=False),
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('type', qos_types),
            sa.Column('description', sa.String(length=255), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    if not migration.schema_has_table("qos_policies"):
        op.create_table(
            'qos_policies',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('qos_id', sa.String(length=36), nullable=False),
            sa.Column('key', sa.String(length=255), nullable=False),
            sa.Column('value', sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(['qos_id'], ['qoses.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', 'qos_id', 'key'),
        )

    if not migration.schema_has_table("networkqosmappings"):
        op.create_table(
            'networkqosmappings',
            sa.Column('network_id', sa.String(length=36), nullable=False,
                      primary_key=True),
            sa.Column('qos_id', sa.String(length=36), nullable=False,
                      primary_key=True),
            sa.ForeignKeyConstraint(['network_id'], ['networks.id'],
                                    ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['qos_id'], ['qoses.id'], ondelete='CASCADE'),
        )

    if not migration.schema_has_table("portqosmappings"):
        op.create_table(
            'portqosmappings',
            sa.Column('port_id', sa.String(length=36), nullable=False),
            sa.Column('qos_id', sa.String(length=36), nullable=False),
            sa.Column('ip_address', sa.String(64), nullable=False),
            sa.ForeignKeyConstraint(['port_id'], ['ports.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['qos_id'], ['qoses.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('port_id', 'qos_id', 'ip_address'),
        )


def downgrade(active_plugins=None, options=None):

    op.drop_table('portqosmappings')
    op.drop_table('networkqosmappings')
    op.drop_table('qos_policies')
    op.drop_table('qoses')
    qos_types.drop(op.get_bind(), checkfirst=False)
