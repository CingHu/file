import random
from sqlalchemy import orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from neutron.db import agents_db 
from neutron.db import agentschedulers_db
from neutron.openstack.common import log
from neutron.clb.common import constants
from neutron.clb.db import models


LOG = log.getLogger(__name__)


class ClbAgentSchedulerDbMixin(agentschedulers_db.AgentSchedulerDbMixin):
    
    def get_agent_for_load_balancer(self, context, load_balancer_id,
                                    active=None):
        query = context.session.query(models.LoadBalancerAgentBinding)
        query =query.options(orm.joinedload('agent'))
        binding_db = query.get(load_balancer_id)
        
        if binding_db:
            if self.is_eligible_agent(active, binding_db.agent):
                return self._make_agent_dict(binding_db.agent)
    
    def get_agents(self, context, active=None, filters=None):
        query = context.session.query(agents_db.Agent)
        query = query.filter_by(
            agent_type=constants.CLB_AGENT_TYPE
        )
        
        if active is not None:
            query = query.filter_by(admin_state_up=active)

        if filters:
            for key, value in filters.iteritems():
                column = getattr(agents_db.Agent, key, None)
                if column:
                    query = query.filter(column.in_(value))
        return [agent
                for agent in query
                if self.is_eligible_agent(active, agent)]

    def list_load_balancers_on_agent(self, context, id):
        load_balancers = []

        query = context.session.query(
            models.LoadBalancerAgentBinding.load_balancer_id
        )
        query = query.filter_by(agent_id=id)
        
        load_balancer_ids = [item[0] for item in query]
        if load_balancer_ids:
            # fixme: self.get_load_balancers not defined after refactor
            load_balancers = self.get_load_balancers(
                context,
                filters={'id': load_balancer_ids}
            )

        return {'load_balancers': load_balancers}

    def _fields(self, resource, fields):
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource


class ClbAgentScheduler(ClbAgentSchedulerDbMixin):
    def schedule(self, context, load_balancer):
        agent = self.get_agent_for_load_balancer(context, load_balancer['id'])
        
        if agent:
            msg = "Load balancer %s has already been hosted by agent %s"
            LOG.debug(msg, load_balancer['id'], agent['id'])
            return
        
        candidates = self.get_agents(context, active=True)
        if not candidates:
            msg = "No active agents for load balancer %s"
            LOG.warn(msg, load_balancer['id'])
            return
        
        #chosen_agent_db = candidates[0]
        #chosen_agent = self._make_agent_dict(agent)

        #for agent_db in candidates[1:]:
        #    agent = self._make_agent_dict(agent)
        #    if (agent['configurations']['running_load_balancers'] <
        #        chosen_agent['configurations']['running_load_balancers']):
        #        chosen_agent_db = agent_db
        #       chosen_agent = agent
        #        break

        chosen_agent_db = random.choice(candidates)
        
        with context.session.begin(subtransactions=True):
            binding = models.LoadBalancerAgentBinding()
            binding.agent = chosen_agent_db
            binding.load_balancer_id = load_balancer['id']    
            context.session.add(binding)
            
            msg = "Load balancer %s is scheduled to clb agent %s"
            LOG.debug(msg, load_balancer['id'], chosen_agent_db.id)

            return self._make_agent_dict(chosen_agent_db)


def get_agent_id_by_host(context, host):
    query = context.session.query(agents_db.Agent)
    query = query.filter_by(host=host)
    query = query.filter_by(agent_type=constants.CLB_AGENT_TYPE)
    
    try:
        agent_db = query.one()
        return agent_db.id
    except NoResultFound:
        msg = "No CLB agent running on host %s"
        LOG.error(msg % host)
    except MultipleResultsFound:
        msg = "More than one agent running on host %s"
        LOG.error(msg % host)


def get_load_balancer_ids_by_agent(context, agent_id):
    query = context.session.query(models.LoadBalancerAgentBinding)
    query = query.filter_by(agent_id=agent_id)
    binding_dbs = query.all()
    load_balancer_ids = [binding_db.load_balancer_id
                         for binding_db in binding_dbs]
    return load_balancer_ids
