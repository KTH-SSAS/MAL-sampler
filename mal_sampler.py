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
    p_networks = binom(n=20, p=0.5)
    def __init__(self, name: str):
        super().__init__(name)
        self.max_associated_networks = 10
        self.p_associated_networks = binom(n=5, p=0.5)
        self.p_unassociated_networks = binom(n=self.max_associated_networks, p=0.99)
        self.associated_networks = set()

    def probability_of_another_network(self):
        return 1 - self.p_associated_networks.cdf(len(self.associated_networks))

    def spawn_network(self):
        print(f'Spawning new network from {self.name}')
        nw = Network(f'Network_{len(self.associated_networks)}_neigbor')
        self.associated_networks.add(nw)
        nw.associated_networks.add(self)
        return nw

    def veto_spawn_network(self):
        return random.random() > self.probability_of_another_network()

    def print(self):
        print(f'Network: {self.name}. Associated networks: {[an.name for an in self.associated_networks]}')

class Model():
    def __init__(self):
        self.networks = list()
        self.hosts = list()

    def veto_add_network(self):
        return random.random() < Network.p_networks.cdf(len(self.networks))

    def add_network(self):
        if self.veto_add_network():
            print(f'Vetoing add network. Number of networks: {len(self.networks)}')
            return None
        else:
            if len(self.networks) == 0:
                nw = Network(f'Network_{len(self.networks)}')
                self.networks.append(nw)
                return nw
            else:
                source_nw = random.choice(self.networks)
                if source_nw.veto_spawn_network():
                    print(f'{source_nw.name} is vetoing spawn network. Number of associated networks: {len(source_nw.associated_networks)}')
                    return None
                else:
                    target_nw = source_nw.spawn_network()
                    self.networks.append(target_nw)
                    return target_nw

    def print(self):
        for nw in self.networks:
            nw.print()

 
class Sampler():
    def __init__(self):
        self.current_model = Model()

    def sample(self):
        self.current_model.add_network()
        self.current_model.print()
        self.current_model.add_network()
        self.current_model.print()
        self.current_model.add_network()
        self.current_model.print()
        self.current_model.add_network()
        self.current_model.print()


if __name__ == "__main__":
    sampler = Sampler()
    sampler.sample()
