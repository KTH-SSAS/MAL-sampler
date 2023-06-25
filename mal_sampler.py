from scipy.stats import rv_discrete, bernoulli, binom
import random

# For all possible actions, compute likelihood of resulting model. 
# Choose action that maximizes likelihood.

class Asset:
    def __init__(self, name: str):
        self.name = name

    def fully_associated(self, associated_asset_type: str):
        return True

    def print(self):
        print(self.name)

class Network(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_associated_networks = binom(n=5, p=0.5).rvs()
        self.n_unassociated_networks = binom(n=10, p=0.5).rvs()
        self.associated_networks = set()
        self.n_associated_hosts = binom(n=10, p=0.5).rvs()
        self.associated_hosts = set()

    def fully_associated(self, associated_asset_type: str):
        if associated_asset_type == 'network':
            return len(self.associated_networks) == self.n_associated_networks
        if associated_asset_type == 'host':
            return len(self.associated_hosts) == self.n_associated_hosts
        raise ValueError(f'Unknown associated asset type: {associated_asset_type}')

    def vote_for_new_network(self, n_networks: int):
        current_associated_networks = len(self.associated_networks)
        current_unassociated_networks = n_networks - current_associated_networks
        target_associated_networks = self.n_associated_networks
        target_unassociated_networks = self.n_unassociated_networks



    def print(self):
        print(f'Network: {self.name}. Number of associated networks: {self.n_associated_networks}, Associated networks: {[an.name for an in self.associated_networks]}')

class Host(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_associated_networks = 1
        self.associated_networks = set()

    def fully_associated(self, associated_asset_type: str):
        if associated_asset_type == 'network':
            return len(self.associated_networks) == self.n_associated_networks
        raise ValueError(f'Unknown associated asset type: {associated_asset_type}')

    def print(self):
        print(f'Host: {self.name}. Number of associated networks: {self.n_associated_networks}, Associated networks: {[an.name for an in self.associated_networks]}')

class Model():
    def __init__(self):
        self.networks = list()
        self.hosts = list()

    def incompletely_associated(self, source_associated_asset_type: str, target_associated_asset_type: str):
        if source_associated_asset_type == 'network':
            return [nw for nw in self.networks if not nw.fully_associated(target_associated_asset_type)]
        if source_associated_asset_type == 'host':
            return [h for h in self.hosts if not h.fully_associated(target_associated_asset_type)]
        raise ValueError(f'Unknown source associated asset type: {source_associated_asset_type}')

    def find_or_create_neighbor(self, source_network: Network):
        assert source_network.n_associated_networks < len(self.networks)
        inc_net =  self.incompletely_associated('network', 'network')
        available_networks = [nw for nw in inc_net if nw not in source_network.associated_networks and nw != source_network]
        if len(available_networks) == 0:
            nw = Network(f'Network_{len(self.networks)}')
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
#    model = Model()
#    model.sample()
    p = binom(n=20, p=0.5).pmf(10)
    print(p)