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

from neutron.openstack.common import jsonutils
from neutron.services.qos.drivers import qos_base


class ChinacQoSDriver(qos_base.QoSDriver):
    # TODO(liuzhikun) implement an ovs_lib class to help maintain qos

    def __init__(self, ext_bridge):
        self.ext_bridge = ext_bridge
        self.ext_port = self.ext_bridge.get_port_name_list()[0]

        self.QOS_UUID = ""
        # TODO: use random int instead of increasing int
        self.TOP_QUEUE_REF = 0
        self.qoses = {}

        self.init_qos()
        self.init_qosqueues()


    def init_qos(self):
        # Initialize QoS setting
        qos_id = ""
        result = self.ext_bridge.run_vsctl(['--format=json',
                                            '--columns=_uuid,external_ids',
                                            'list', 'qos'],
                                           check_error=True)
        res = jsonutils.loads(result)
        if res['data']:
            qos_id = res['data'][0][0][1]

        if qos_id:
            self.QOS_UUID = qos_id
        else:
            # create default qos and queue
            result = self.ext_bridge.run_vsctl(['--',
                            "--id=@qosid", 'create', 'qos', "type=linux-htb",
                            "external_ids:top_queue_ref=0","queues=0=@q0",
                            '--', "--id=@q0", 'create', 'queue',
                            "other-config:min-rate=1000000000",
                            "other-config:max-rate=1000000000"],
                            check_error=True)
            self.QOS_UUID = result.split()[0]

        # set qos in external port
        self.ext_bridge.run_vsctl(['add', 'port', self.ext_port,
                                   'qos', self.QOS_UUID],
                                  check_error=True)

        result = self.ext_bridge.db_get_map('qos',
                                            self.QOS_UUID,
                                            'external_ids')
        self.TOP_QUEUE_REF = int(result['top_queue_ref'])

    def init_qosqueues(self):
        # Initialize QoS queues for ports
        result = self.ext_bridge.run_vsctl(['--format=json',
                                            '--columns=_uuid',
                                            'list', 'queue'],
                                           check_error=True)
        res = jsonutils.loads(result)
        if not res['data']:
            return

        for qid in res['data'][0]:
            result = self.ext_bridge.db_get_map('queue', qid[1],
                                                'external_ids',
                                                check_error=True)
            if not hasattr(result, 'port_id'):
                continue
            qos_key = "%s-%s" % (result['port_id'], result['ip_address'])
            self.qoses[qos_key] = True


    def _create_queue_for_port(self, policy, port_id, ip_address):
        self.TOP_QUEUE_REF += 1
        result = self.ext_bridge.run_vsctl(['create', 'queue',
                            "other-config:min-rate=%s" % policy['max_rate'],
                            "other-config:max-rate=%s" % policy['max_rate'],
                            "external_ids:port_id=%s" % port_id,
                            "external_ids:ip_address=%s" % ip_address,
                            "external_ids:queue_ref=%s" % self.TOP_QUEUE_REF],
                            check_error=True)
        queue_id = result.strip()
        self.ext_bridge.run_vsctl(['add', 'qos', self.QOS_UUID, 'queues',
                        "%s=%s" % (self.TOP_QUEUE_REF, queue_id),
                        '--', 'set', 'qos', self.QOS_UUID,
                        "external_ids:top_queue_ref=%s" % self.TOP_QUEUE_REF],
                        check_error=True)
        return self.TOP_QUEUE_REF

    def _delete_queue_for_port(self, policy, port_id, ip_address):
        result = self.ext_bridge.run_vsctl(['--format=json', '--columns=_uuid',
                                   'find', 'queue',
                                   "other-config:min-rate=%s" % policy['max_rate'],
                                   "other-config:max-rate=%s" % policy['max_rate'],
                                   "external_ids:port_id=%s" % port_id,
                                   "external_ids:ip_address=%s" % ip_address],
                                   check_error=True)
        res = jsonutils.loads(result)
        if not res['data']:
            return

        queue_id = res['data'][0][0][1]
        result = self.ext_bridge.db_get_map("queue", queue_id,
                                            'external_ids',
                                            check_error=True)
        queue = "%s=%s" % (result['queue_ref'], queue_id)
        # Remove queue from Qos
        self.ext_bridge.run_vsctl(['remove', 'qos', self.QOS_UUID,
                                   'queues', queue])
        # Delete queue
        self.ext_bridge.run_vsctl(['destroy', 'queue', queue_id])

    def create_qos_for_port(self, policy, port_id, ip_address):
        qos_key = "%s-%s" % (port_id, ip_address)
        ofport = self.ext_bridge.get_vif_port_by_id(port_id).ofport
        queue_ref = self._create_queue_for_port(policy, port_id, ip_address)
        action = "set_queue:%s,NORMAL" % queue_ref
        self.ext_bridge.add_flow(in_port=ofport, nw_src=ip_address,
                                 proto=policy['protocol'],
                                 actions=action, priority=65535)

        self.qoses[qos_key] = True

    def delete_qos_for_port(self, policy, port_id, ip_address):
        qos_key = "%s-%s" % (port_id, ip_address)
        if qos_key not in self.qoses:
            return
        ofport = self.ext_bridge.get_vif_port_by_id(port_id).ofport
        self.ext_bridge.delete_flows(in_port=ofport,
                                     proto=policy['protocol'],
                                     nw_src=ip_address)
        self._delete_queue_for_port(policy, port_id, ip_address)
        del self.qoses[qos_key]

    def port_qos_updated(self, policy, port_id, ip_address):
        # Remove flow, create new one with the updated policy
        self.delete_qos_for_port(policy, port_id, ip_address)
        self.create_qos_for_port(policy, port_id, ip_address)

    def create_qos_for_network(self, policy, network_id):
        pass

    def delete_qos_for_network(self, network_id):
        pass

    def network_qos_updated(self, policy, network_id):
        pass