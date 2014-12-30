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
#

"""portforwardings

Revision ID: 3f262f6b0251
Revises: juno
Create Date: 2014-11-27 10:50:41.812647

"""

# revision identifiers, used by Alembic.
revision = '3f262f6b0251'
down_revision = 'juno'

from alembic import op
import sqlalchemy as sa

from neutron.db import migration


def upgrade(active_plugins=None, options=None):
    if migration.schema_has_table('portforwardingrules'):
        return

    op.create_table('portforwardingrules',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('router_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('outside_port', sa.String(length=11), nullable=True),
                    sa.Column('inside_addr', sa.String(length=15),
                              nullable=True),
                    sa.Column('inside_port', sa.String(length=11), nullable=True),
                    sa.Column('protocol', sa.String(length=4),
                              nullable=True),
                    sa.Column('status', sa.String(length=8),
                              nullable=True),
                    sa.ForeignKeyConstraint(['router_id'], ['routers.id'],
                                            ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('router_id', 'protocol',
                                        'outside_port',
                                        name='rule'),
                    )


def downgrade(active_plugins=None, options=None):
    if not migration.schema_has_table('portforwardingrules'):
        return

    op.drop_table('portforwardingrules')
