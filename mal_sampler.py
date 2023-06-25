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
        self.max_associated_networks = 10
        self.p_associated_networks = binom(n=5, p=0.5)
        self.p_unassociated_networks = binom(n=self.max_associated_networks, p=0.99)
        self.associated_networks = set()

    def spawn_network(self):
        nw = Network(f'Network_{len(self.associated_networks)}')
        self.associated_networks.add(nw)
        nw.associated_networks.add(self)
        return nw

    def normalized_log_probability(self, model):
        logp_of_assoc = self.p_associated_networks.logpmf(len(self.associated_networks))
        logp_of_unassoc = self.p_unassociated_networks.logpmf(len(model.networks) - len(self.associated_networks))
        n_possible_configurations = len(model.networks)*(len(model.networks))/2
        print(f'log(n_possible_configurations) {math.log(self.max_associated_networks)}. log prob {logp_of_assoc} of {len(self.associated_networks)} associated networks. log prob {logp_of_unassoc} of {len(model.networks) - len(self.associated_networks)} unassociated networks.')
        return math.log(self.max_associated_networks) + self.p_associated_networks.logpmf(len(self.associated_networks)) + self.p_unassociated_networks.logpmf(len(model.networks) - len(self.associated_networks))

    def print(self):
        print(f'Network: {self.name}. Associated networks: {[an.name for an in self.associated_networks]}')

class Model():
    def __init__(self):
        self.networks = list()
        self.hosts = list()

    def probability(self):
        if self.networks:
            log_probability = 0
            for nw in self.networks:
                log_probability += nw.normalized_log_probability(self)
            return log_probability
        else:
            return float('-inf')

    def add_network(self):
        if len(self.networks) == 0:
            nw = Network(f'Network_{len(self.networks)}')
            self.networks.append(nw)
            return nw
        else:
            nw = random.choice(self.networks)
            self.networks.append(nw.spawn_network())
            return nw

    def print(self):
        for nw in self.networks:
            nw.print()

 
class Sampler():
    def __init__(self):
        self.current_model = Model()

    def sample(self):
        print(f'Initial probability: {self.current_model.probability()}')
        self.current_model.add_network()
        print(f'One network probability: {self.current_model.probability()}')
        self.current_model.add_network()
        print(f'Two network probability: {self.current_model.probability()}')
        self.current_model.add_network()
        print(f'Three network probability: {self.current_model.probability()}')
        self.current_model.print()

if __name__ == "__main__":
    sampler = Sampler()
    sampler.sample()
