from scipy.stats import binom
import random
import networkx as nx
import matplotlib.pyplot as plt
import sys

# For all possible actions, compute likelihood of resulting model.
# Choose action that maximizes likelihood.


class Asset:
    def __init__(self, name: str, asset_type_name: str):
        self.name = name
        self.asset_type_name = asset_type_name
        self.n_associated_assets = dict()
        self.associated_assets = dict()

    def accepts(self, asset_type: str):
        return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type]

    def print(self):
        print(f"{self.asset_type_name}: {self.name}. Associated assets: {[(n, [a.name for a in list(self.associated_assets[n])]) for n in self.associated_assets]}")


class Network(Asset):
    def __init__(self, name: str):
        super().__init__(name, 'network')
        self.n_associated_assets['network'] = 1 + binom(n=500, p=0.005).rvs()
        self.n_associated_assets['vm_instance'] = 1 + binom(n=1000, p=0.005).rvs()
        self.associated_assets['network'] = set()
        self.associated_assets['vm_instance'] = set()

class VMInstance(Asset):
    def __init__(self, name: str):
        super().__init__(name, 'vm_instance')
        self.n_associated_assets['network'] = 1
        self.n_associated_assets['admin'] = 1
        self.associated_assets['network'] = set()
        self.associated_assets['admin'] = set()
    

class Principal(Asset):
    def __init__(self, name: str):
        super().__init__(name, 'principal')
        self.n_associated_assets['admin'] = binom(n=2, p=0.1).rvs()
        self.associated_assets['admin'] = set()


class Role(Asset):
    def __init__(self, name: str, asset_type_name: str):
        super().__init__(name, asset_type_name)
        self.associated_assets['vm_instance'] = set()
        self.associated_assets['principal'] = set()


class ComputeOSAdminLogin(Role):
    def __init__(self, name: str):
        super().__init__(name, 'admin')
        self.n_associated_assets['vm_instance'] = 1
        self.n_associated_assets['principal'] = 1 + binom(n=5, p=0.1).rvs()


class ComputeOSLogin(Role):
    def __init__(self, name: str):
        super().__init__(name, 'login')
        self.n_associated_assets['vm_instance'] = binom(n=30, p=0.5).rvs()
        self.n_associated_assets['principal'] = 1 + binom(n=5, p=0.1).rvs()


class Model():
    def __init__(self):
        self.n_assets = dict()
        self.assets = dict()
        self.n_assets['network'] = 1 + binom(n=30, p=0.5).rvs()
        self.n_assets['principal'] = 1 + binom(n=10*self.n_assets['network'], p=0.05).rvs()
        self.n_assets['vm_instance'] = 200
        self.n_assets['admin'] = sys.maxsize
        self.n_assets['login'] = sys.maxsize
        self.assets['network'] = set()
        self.assets['vm_instance'] = set()
        self.assets['principal'] = set()
        self.assets['admin'] = set()

    def add(self, asset_type: str):
        a = None
        if len(self.assets[asset_type]) < self.n_assets[asset_type]:
            if asset_type == 'network':
                a = Network(f"N{len(self.assets[asset_type])}")
            elif asset_type == 'principal':
                a = Principal(f"P{len(self.assets[asset_type])}")
            elif asset_type == 'vm_instance':
                a = VMInstance(f"VM{len(self.assets[asset_type])}")
            elif asset_type == 'admin':
                a = ComputeOSAdminLogin(f"A{len(self.assets[asset_type])}")
            elif asset_type == 'login':
                a = ComputeOSLogin(f"L{len(self.assets[asset_type])}")
            else:
                raise ValueError(f'Unknown asset type: {asset_type}')
            self.assets[asset_type].add(a)
        else:
            print(f'Reached the limit of {self.n_assets[asset_type]} {asset_type} assets.')
        return a

    def associate_networks_to_networks(self):
        available_networks = [nw for nw in self.assets['network'] if nw.accepts('network')]
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

    def associate(self, source_asset_type: str, target_asset_type: str):
        print(f'Attempting to associate some {source_asset_type} to some {target_asset_type}')
        available_source_assets = [a for a in self.assets[source_asset_type] if a.accepts(target_asset_type)]
        if len(available_source_assets) > 0:
            print(f'Found {len(available_source_assets)} {source_asset_type} to associate to {target_asset_type}')
            source_asset = random.choice(available_source_assets)
        else:
            print(f'Not enough {source_asset_type} to associate to {target_asset_type}. Creating one.')
            source_asset = self.add(source_asset_type)
        if not source_asset:  
            print(f'Could not find or create source {source_asset_type} to associate to {target_asset_type}') 
            return False
        else:
            available_target_assets = [a for a in self.assets[target_asset_type] if a.accepts(source_asset_type) and a not in source_asset.associated_assets[target_asset_type]]
            if len(available_target_assets) > 0:
                target_asset = random.choice(available_target_assets)
            else:
                print(f'Not enough {target_asset_type} to associate to {source_asset_type}. Creating one.')
                target_asset = self.add(target_asset_type)

            if target_asset:
                source_asset.associated_assets[target_asset_type].add(target_asset)
                target_asset.associated_assets[source_asset_type].add(source_asset)
                print(f'Associated {source_asset.name} to {target_asset.name}')
                return True
            else:
                print(f'Could not find or create target {target_asset_type} to associate to {source_asset_type}') 
                return False

    def print(self):
        for asset_type in self.assets.keys():
            for asset in self.assets[asset_type]:
                asset.print()

    def plot(self):
        G = nx.Graph()
        for vm in self.assets['vm_instance']:
            G.add_node(vm.name)
        for a in self.assets['admin']:
            G.add_node(a.name)
        for nw in self.assets['network']:
            G.add_node(nw.name)
            for an in nw.associated_assets['network']:
                G.add_edge(nw.name, an.name)
            for ah in nw.associated_assets['vm_instance']:
                G.add_edge(nw.name, ah.name)
                for a in ah.associated_assets['admin']:
                    G.add_edge(ah.name, a.name)
        for p in self.assets['principal']:
            G.add_node(p.name)
        pos = nx.spring_layout(G, k=0.125, iterations=50)
        plt.figure(facecolor='black')
        nx.draw_networkx_nodes(G, pos, nodelist=[nw.name for nw in self.assets['network']], node_shape='s', node_color='red', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[ah.name for ah in self.assets['vm_instance']], node_shape='o', node_color='blue', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[p.name for p in self.assets['principal']], node_shape='^', node_color='green', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[a.name for a in self.assets['admin']], node_shape='v', node_color='yellow', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_edges(G, pos, edge_color='white', width=0.5)
        nx.draw_networkx_labels(G, pos, font_color='white', font_size=2)
        plt.axis('off')
        plt.savefig('model.png', dpi=1200, bbox_inches='tight', pad_inches = 0, facecolor='black') 


class Sampler():
    def __init__(self):
        self.current_model = Model()

    def sample(self):
        print('Adding networks')
        while self.current_model.add('network'):
            pass
        print('Adding principals')
        while self.current_model.add('principal'):
            pass
        print('Associating networks to networks')
        while self.current_model.associate_networks_to_networks() > 1:
            pass
        while self.current_model.associate('vm_instance', 'network'):
            pass
        while self.current_model.associate('vm_instance', 'admin') > 0:
            pass
        self.current_model.print()
        self.current_model.plot()

if __name__ == "__main__":
    sampler = Sampler()
    sampler.sample()
