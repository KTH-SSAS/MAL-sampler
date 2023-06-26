from scipy.stats import binom
import random
import networkx as nx
import matplotlib.pyplot as plt

# For all possible actions, compute likelihood of resulting model.
# Choose action that maximizes likelihood.


class Asset:
    def __init__(self, name: str):
        self.name = name
        self.n_associated_assets = dict()
        self.associated_assets = dict()

    def accepts(self, asset_type: str):
        return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type]

    def print(self):
        print(self.name)


class Network(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        # self.n_networks = 1 + binom(n=500, p=0.005).rvs()
        # self.networks = set()
        # self.n_vm_instances = 1 + binom(n=1000, p=0.005).rvs()
        # self.vm_instances = set()
        self.n_associated_assets['network'] = 1 + binom(n=500, p=0.005).rvs()
        self.n_associated_assets['vm_instance'] = 1 + binom(n=1000, p=0.005).rvs()
        self.associated_assets['network'] = set()
        self.associated_assets['vm_instance'] = set()

    # def accepts_network(self):
    #     return len(self.networks) < self.n_networks

    # def accepts_vm_instance(self):
    #     return len(self.vm_instances) < self.n_vm_instances

    def print(self):
        print(f"Network: {self.name}. Associated networks: {[an.name for an in self.associated_assets['network']]}. Associated VM instances: {[ah.name for ah in self.associated_assets['vm_instance']]}")


class VMInstance(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_networks = 1
        self.n_admins = 1
        self.networks = set()
        self.admins = set()

    def accepts_network(self):
        return len(self.networks) < self.n_networks

    def accepts_admin(self):
        return len(self.admins) < self.n_admins
    
    def print(self):
        print(
            f'VMInstance: {self.name}. Networks: {[nw.name for nw in self.networks]}')


class Principal(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_admins = 1
        self.admins = set()

    def accepts_admin(self):
        return len(self.admins) < self.n_admins


class Role(Asset):
    def __init__(self, name: str):
        super().__init__(name)
        self.vm_instances = set()
        self.principals = set()


class ComputeOSAdminLogin(Role):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_vm_instances = 1
        self.n_principal = 1 + binom(n=5, p=0.1).rvs()

    def accepts_principal(self):
        return len(self.principals) < self.n_principal


class ComputeOSLogin(Role):
    def __init__(self, name: str):
        super().__init__(name)
        self.n_vm_instances = binom(n=30, p=0.5).rvs()
        self.n_principal = 1 + binom(n=5, p=0.1).rvs()


class Model():
    def __init__(self):
        self.n_networks = 1 + binom(n=30, p=0.5).rvs()
        self.n_principals = 1 + binom(n=10*self.n_networks, p=0.05).rvs()
        self.networks = set()
        self.vm_instances = set()
        self.principals = set()
        self.admins = set()

    def add_network(self):
        if len(self.networks) <= self.n_networks:
            nw = Network(f'N{len(self.networks)}')
            self.networks.add(nw)
        else:
            print('Cannot add more networks')
        return self.n_networks - len(self.networks)

    def add_principal(self):
        if len(self.principals) <= self.n_principals:
            principal = Principal(f'P{len(self.principals)}')
            self.principals.add(principal)
        else:
            print('Cannot add more principals')
        return self.n_principals - len(self.principals)

    def associate_networks_to_networks(self):
        available_networks = [nw for nw in self.networks if nw.accepts('network')]
        if len(available_networks) < 2:
            print('Not enough networks to associate to each other')
            return len(available_networks)
        else:
            source_nw = random.choice(available_networks)
            target_nw = random.choice([nw for nw in available_networks if nw != source_nw])
            if source_nw in target_nw.associated_assets['network'] or target_nw in source_nw.associated_assets['network']:
                print(f'Networks already associated. {len(available_networks)} networks left.')
                return len(available_networks) - 1
            else:
                source_nw.associated_assets['network'].add(target_nw)
                target_nw.associated_assets['network'].add(source_nw)
                print(
                    f'Associated {source_nw.name} to {target_nw.name}. {len(available_networks)} networks left.')
                return len(available_networks)

    def associate_vm_instances_to_networks(self):
        available_networks = [nw for nw in self.networks if nw.accepts('vm_instance')]
        if len(available_networks) == 0:
            print('Not enough networks to associate vm instances to')
        else:
            nw = random.choice(available_networks)
            vm_instance = VMInstance(f'VM{len(self.vm_instances)}')
            self.vm_instances.add(vm_instance)
            nw.associated_assets['vm_instance'].add(vm_instance)
            vm_instance.networks.add(nw)
        return len(available_networks)

    def associate_admins_to_vm_instances(self):
        available_vm_instances = [vm for vm in self.vm_instances if vm.accepts_admin()]
        if len(available_vm_instances) == 0:
            print('Not enough VM instances to associate admins to')
        else:
            ah = random.choice(available_vm_instances)
            admin = ComputeOSAdminLogin(f'A{ah.name}')
            self.admins.add(admin)
            ah.admins.add(admin)
            admin.vm_instances.add(ah)
        return len(available_vm_instances)

    def associate_principals_to_admins(self):
        available_admins = [a for a in self.admins if a.accepts_principal()]
        available_principal = [p for p in self.principals if p.accepts_admin()]
        if len(available_admins) == 0:
            print('Not enough admins to associate principals to')
        else:
            a = random.choice(available_admins)
            p = random.choice([p for p in self.principals if p not in a.principals])
            a.principals.add(p)
            p.admins.add(a)
        return len(available_admins)

    def print(self):
        for nw in self.networks:
            nw.print()

    def plot(self):
        G = nx.Graph()
        for nw in self.networks:
            G.add_node(nw.name)
            for an in nw.associated_assets['network']:
                G.add_edge(nw.name, an.name)
            for ah in nw.associated_assets['vm_instance']:
                G.add_edge(nw.name, ah.name)
                for a in ah.admins:
                    G.add_edge(ah.name, a.name)
        for p in self.principals:
            G.add_node(p.name)
        pos = nx.spring_layout(G, k=0.125, iterations=50)
        plt.figure(facecolor='black')
        nx.draw_networkx_nodes(G, pos, nodelist=[nw.name for nw in self.networks], node_shape='s', node_color='red', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[ah.name for ah in self.vm_instances], node_shape='o', node_color='blue', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[p.name for p in self.principals], node_shape='^', node_color='green', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[a.name for a in self.admins], node_shape='v', node_color='yellow', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_edges(G, pos, edge_color='white', width=0.5)
        nx.draw_networkx_labels(G, pos, font_color='white', font_size=2)
        plt.axis('off')
        plt.savefig('model.png', dpi=1200, bbox_inches='tight', pad_inches = 0, facecolor='black') 


class Sampler():
    def __init__(self):
        self.current_model = Model()

    def sample(self):
        print('Adding networks')
        while self.current_model.add_network() > 0:
            pass
        print('Adding principals')
        while self.current_model.add_principal() > 0:
            pass
        print('Associating networks to networks')
        while self.current_model.associate_networks_to_networks() > 1:
            pass
        print('Associating VM instances to networks')
        while self.current_model.associate_vm_instances_to_networks() > 0:
            pass
        print('Associating admins to VM instances')
        while self.current_model.associate_admins_to_vm_instances() > 0:
            pass
        self.current_model.print()
        self.current_model.plot()

if __name__ == "__main__":
    sampler = Sampler()
    sampler.sample()
