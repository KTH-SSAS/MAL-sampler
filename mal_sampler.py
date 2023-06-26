from scipy.stats import rv_discrete, bernoulli, binom
import random
import math

# For all possible actions, compute likelihood of resulting model. 
# Choose action that maximizes likelihood.

class Asset:
    def __init__(self, name: str):
        self.name = name

    def log_probability(self):
        return float('-inf')


    def print(self):
        print(self.name)

class Network(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_networks = 1 + binom(n=5, p=0.5).rvs()
        self.networks = set()
        self.n_hosts = 1 + binom(n=10, p=0.5).rvs()
        self.hosts = set()

    def accepts_network(self):
        return len(self.networks) < self.n_networks

    def accepts_host(self):
        return len(self.hosts) < self.n_hosts

    def print(self):
        print(f'Network: {self.name}. Associated networks: {[an.name for an in self.networks]}. Associated hosts: {[ah.name for ah in self.hosts]}')


class Host(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_networks = 1
        self.networks = set()

    def accepts_network(self):
        return len(self.networks) < self.n_networks

    def print(self):
        print(f'Host: {self.name}. Networks: {[nw.name for nw in self.networks]}')


class Model():
    def __init__(self):
        self.n_networks = 1 + binom(n=30, p=0.5).rvs()
        self.networks = set()
        self.hosts = set()

    def add_network(self):
        if len(self.networks) <= self.n_networks:
            nw = Network(f'Network_{len(self.networks)}')
            self.networks.add(nw)
        else:
            print('Cannot add more networks')
        return self.n_networks - len(self.networks)
 
    def associate_networks_to_networks(self):
        available_networks = [nw for nw in self.networks if nw.accepts_network()]
        if len(available_networks) < 2:
            print('Not enough networks to associate to each other')
            return len(available_networks)
        else:
            source_nw = random.choice(available_networks)
            target_nw = random.choice([nw for nw in available_networks if nw != source_nw])
            if source_nw in target_nw.networks or target_nw in source_nw.networks:
                print('Networks already associated')
                return len(available_networks) - 1
            else:
                source_nw.networks.add(target_nw)
                target_nw.networks.add(source_nw)
                print(f'Associated {source_nw.name} to {target_nw.name}. {len(available_networks)} networks left')
                return len(available_networks)

    def associate_hosts_to_networks(self):
        available_networks = [nw for nw in self.networks if nw.accepts_host()]
        if len(available_networks) == 0:
            print('Not enough networks to associate hosts to')
        else:
            nw = random.choice(available_networks)
            host = Host(f'Host_{len(self.hosts)}')
            self.hosts.add(host)
            nw.hosts.add(host)
            host.networks.add(nw)
        return len(available_networks)

    def print(self):
        for nw in self.networks:
            nw.print()

 
class Sampler():
    def __init__(self):
        self.current_model = Model()

    def sample(self):
        print('Adding networks')
        while self.current_model.add_network() > 0:
            pass
        print('Associating networks to networks')
        while self.current_model.associate_networks_to_networks() > 1:
            pass
        print('Associating hosts to networks')
        while self.current_model.associate_hosts_to_networks() > 0:
            pass
        self.current_model.print()
 
if __name__ == "__main__":
    sampler = Sampler()
    sampler.sample()
