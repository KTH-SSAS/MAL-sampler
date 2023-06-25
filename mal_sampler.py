from scipy.stats import rv_discrete, bernoulli, binom
import random

class Asset:
    def __init__(self, name: str):
        self.name = name

    def print(self):
        print(self.name)

class Network(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_associated_networks = binom(n=5, p=0.5).rvs()
        self.associated_networks = set()

    def print(self):
        print(f'Network: {self.name}. Number of associated networks: {self.n_associated_networks}, Associated networks: {[an.name for an in self.associated_networks]}')


class Model():
    def __init__(self):
        self.networks = list()

    def incomplete_networks(self):
        return [nw for nw in self.networks if len(nw.associated_networks) < nw.n_associated_networks]

    def find_or_create_neighbor(self, source_network: Network):
        print(f'Total number of networks: {len(self.networks)} of which {len(self.incomplete_networks())} are incomplete')
        print(f'Finding neighbor for network {source_network.name}, currently associated with {len(source_network.associated_networks)} networks and aiming for {source_network.n_associated_networks} associated networks')
        assert source_network.n_associated_networks < len(self.networks)
        inc_net =  self.incomplete_networks()
        available_networks = [nw for nw in inc_net if nw not in source_network.associated_networks and nw != source_network]
        print(f'Number of available networks: {len(available_networks)}', flush=True)
        if len(available_networks) == 0:
            nw = Network(f'Network_{len(self.networks)}')
            print(f'Creating new network: {nw.name}')
            self.networks.append(nw)
            return nw
        return random.choice(available_networks)

    def associate_networks(self, source_network: Network):
        for i in range(len(source_network.associated_networks), source_network.n_associated_networks + 1):
            if source_network.n_associated_networks > len(source_network.associated_networks):
                nw = self.find_or_create_neighbor(source_network)
                source_network.associated_networks.add(nw)
                nw.associated_networks.add(source_network)

    def print(self):
        for nw in self.networks:
            nw.print()

    def sample(self):
        n_networks = binom(n=20, p=0.5).rvs()
        for i in range(n_networks):
            nw = Network(f'Network_{len(self.networks)}')
            self.networks.append(nw)

        for nw in self.networks:
            self.associate_networks(nw)

        self.print()

if __name__ == "__main__":
    model = Model()
    model.sample()