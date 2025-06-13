from athos.core.agent_base import Agent
from athos.tools.slurm_query import query_jobs

class HPCSmolAgent(Agent):
    def run(self):
        jobs = query_jobs(user="demo")
        print("HPC agent sees jobs:", jobs)
