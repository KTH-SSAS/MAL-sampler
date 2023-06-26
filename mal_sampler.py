from scipy.stats import binom
import random
import networkx as nx
import matplotlib.pyplot as plt

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
        self.n_networks = 1 + binom(n=500, p=0.005).rvs()
        self.networks = set()
        self.n_vm_instances = 1 + binom(n=1000, p=0.005).rvs()
        self.vm_instances = set()

    def accepts_network(self):
        return len(self.networks) < self.n_networks

    def accepts_vm_instance(self):
        return len(self.vm_instances) < self.n_vm_instances

    def print(self):
        print(
            f'Network: {self.name}. Associated networks: {[an.name for an in self.networks]}. Associated VM instances: {[ah.name for ah in self.vm_instances]}')


class VMInstance(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_networks = 1
        self.networks = set()

    def accepts_network(self):
        return len(self.networks) < self.n_networks

    def print(self):
        print(
            f'VMInstance: {self.name}. Networks: {[nw.name for nw in self.networks]}')


class Model():
    def __init__(self):
        self.n_networks = 1 + binom(n=30, p=0.5).rvs()
        self.networks = set()
        self.vm_instances = set()

    def add_network(self):
        if len(self.networks) <= self.n_networks:
            nw = Network(f'Network_{len(self.networks)}')
            self.networks.add(nw)
        else:
            print('Cannot add more networks')
        return self.n_networks - len(self.networks)

    def associate_networks_to_networks(self):
        available_networks = [
            nw for nw in self.networks if nw.accepts_network()]
        if len(available_networks) < 2:
            print('Not enough networks to associate to each other')
            return len(available_networks)
        else:
            source_nw = random.choice(available_networks)
            target_nw = random.choice(
                [nw for nw in available_networks if nw != source_nw])
            if source_nw in target_nw.networks or target_nw in source_nw.networks:
                print(f'Networks already associated. {len(available_networks)} networks left.')
                return len(available_networks) - 1
            else:
                source_nw.networks.add(target_nw)
                target_nw.networks.add(source_nw)
                print(
                    f'Associated {source_nw.name} to {target_nw.name}. {len(available_networks)} networks left.')
                return len(available_networks)

    def associate_vm_instances_to_networks(self):
        available_networks = [nw for nw in self.networks if nw.accepts_vm_instance()]
        if len(available_networks) == 0:
            print('Not enough networks to associate vm instances to')
        else:
            nw = random.choice(available_networks)
            vm_instance = VMInstance(f'VM_{len(self.vm_instances)}')
            self.vm_instances.add(vm_instance)
            nw.vm_instances.add(vm_instance)
            vm_instance.networks.add(nw)
        return len(available_networks)

    def print(self):
        for nw in self.networks:
            nw.print()

    def plot(self):
        G = nx.Graph()
        for nw in self.networks:
            G.add_node(nw.name)
            for an in nw.networks:
                G.add_edge(nw.name, an.name)
            for ah in nw.vm_instances:
                G.add_edge(nw.name, ah.name)
        pos = nx.spring_layout(G)
        plt.figure(facecolor='black')
        nx.draw_networkx_nodes(G, pos, nodelist=[nw.name for nw in self.networks], node_shape='s', node_color='red', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[ah.name for ah in self.vm_instances], node_shape='o', node_color='blue', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_edges(G, pos, edge_color='white', width=0.5)
        nx.draw_networkx_labels(G, pos, font_color='white', font_size=4)
        plt.axis('off')
        plt.savefig('model.png', dpi=600, bbox_inches='tight', pad_inches = 0, facecolor='black') 

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
        print('Associating VM instances to networks')
        while self.current_model.associate_vm_instances_to_networks() > 0:
            pass
        self.current_model.print()
        self.current_model.plot()

if __name__ == "__main__":
    sampler = Sampler()
    sampler.sample()
