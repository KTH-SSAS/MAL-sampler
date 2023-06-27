from scipy.stats import binom
import random
import networkx as nx
import matplotlib.pyplot as plt
import sys


class Asset:
    def __init__(self, name: str, asset_type_name: str):
        self.name = name
        self.asset_type_name = asset_type_name
        self.n_associated_assets = dict()
        self.associated_assets = dict()

    def accepts(self, asset_type: str):
        return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type]

    def print(self):
        print(
            f"{self.asset_type_name}: {self.name}. Associated assets: {[(n, [a.name for a in list(self.associated_assets[n])]) for n in self.associated_assets]}")


class Model:
    def __init__(self, metamodel: dict):
        self.n_assets = dict()
        self.assets = dict()
        self.metamodel = metamodel
        for asset_type in self.metamodel:
            self.n_assets[asset_type] = self.sample_distribution(self.metamodel[asset_type]['n'])
            self.assets[asset_type] = set()
            print(f'self.n_assets[{asset_type}]: n = {self.n_assets[asset_type]}.')

    def sample_distribution(self, distribution_dict: dict):
        if distribution_dict['distribution'] == 'Binomial':
            return binom(n=distribution_dict['n'], p=distribution_dict['p']).rvs()
        elif distribution_dict['distribution'] == 'Constant':
            return distribution_dict['n']
        elif distribution_dict['distribution'] == 'BinomialPlusOne':
            return binom(n=distribution_dict['n'], p=distribution_dict['p']).rvs() + 1       

    def add(self, asset_type: str):
        if len(self.assets[asset_type]) < self.n_assets[asset_type]:
            if asset_type in self.metamodel:
                abbreviation = self.metamodel[asset_type]['abbreviation']
                a = Asset(f"{abbreviation}{len(self.assets[asset_type])}", asset_type)
                for asset_name, dist_dict in self.metamodel[asset_type]['associated_assets'].items():
                    a.n_associated_assets[asset_name] = self.sample_distribution(dist_dict)
                    a.associated_assets[asset_name] = set()
            else:
                raise ValueError(f'Unknown asset type: {asset_type}')
            self.assets[asset_type].add(a)
            print(f'Added asset {a.name} of type {a.asset_type_name}.')
            a.print()
            return a
        else:
            print(
                f'Reached the limit of {self.n_assets[asset_type]} {asset_type} assets.')
            return None

    def associate(self, source_asset_type: str, target_asset_type: str):
        print(
            f'Attempting to associate some {source_asset_type} to some {target_asset_type}')
        available_source_assets = [
            a for a in self.assets[source_asset_type] if a.accepts(target_asset_type)]
        if len(available_source_assets) == 0:
            print(
                f'Could not find, and would not create, source {source_asset_type} to associate to {target_asset_type}')
            return False
        else:
            print(
                f'Found {len(available_source_assets)} {source_asset_type} to associate to {target_asset_type}')
            source_asset = random.choice(available_source_assets)

            available_target_assets = [
                a for a in self.assets[target_asset_type] if a.accepts(source_asset_type)]
            available_target_assets = [
                a for a in available_target_assets if a not in source_asset.associated_assets[target_asset_type]]
            if target_asset_type == source_asset_type:
                available_target_assets = [
                    a for a in available_target_assets if a != source_asset]
            print(
                f'Found {len(available_target_assets)} {target_asset_type} to associate to {source_asset_type}')
            if len(available_target_assets) > 0:
                target_asset = random.choice(available_target_assets)
            else:
                print(
                    f'Not enough {target_asset_type} to associate to {source_asset_type}. Attempting to create one.')
                target_asset = self.add(target_asset_type)

            if target_asset:
                source_asset.associated_assets[target_asset_type].add(
                    target_asset)
                target_asset.associated_assets[source_asset_type].add(
                    source_asset)
                print(f'Associated {source_asset.name} to {target_asset.name}')
                return True
            else:
                print(
                    f'Could not find or create target {target_asset_type} to associate to {source_asset_type}')
                return False

    def print(self):
        for asset_type in self.assets.keys():
            for asset in self.assets[asset_type]:
                asset.print()

    def plot(self):
        G = nx.Graph()
        for asset_type_name in self.assets.keys():
            for asset in self.assets[asset_type_name]:
                G.add_node(asset.name)
                for associated_asset_type_name in asset.associated_assets.keys():
                    for associated_asset in asset.associated_assets[associated_asset_type_name]:
                        G.add_edge(asset.name, associated_asset.name)
        pos = nx.spring_layout(G, k=0.25, iterations=50)
        plt.figure(facecolor='black')
        nx.draw_networkx_nodes(G, pos, nodelist=[nw.name for nw in self.assets['network']],
                               node_shape='s', node_color='red', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[ah.name for ah in self.assets['vm_instance']],
                               node_shape='o', node_color='blue', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[p.name for p in self.assets['principal']],
                               node_shape='^', node_color='green', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_nodes(G, pos, nodelist=[a.name for a in self.assets['admin']],
                               node_shape='v', node_color='yellow', edgecolors='white', linewidths=0.5, node_size=50)
        nx.draw_networkx_edges(G, pos, edge_color='white', width=0.5)
        nx.draw_networkx_labels(G, pos, font_color='white', font_size=2)
        plt.axis('off')
        plt.savefig('model.png', dpi=1200, bbox_inches='tight',
                    pad_inches=0, facecolor='black')


class Sampler():
    def __init__(self, metamodel: dict):
        self.model = Model(metamodel)

    def sample(self):
        print('Adding networks')
        while self.model.add('network'):
            print(f'Added {len(self.model.assets["network"])} networks')
        print('Adding principals')
        while self.model.add('principal'):
            pass
        print('Associating networks to networks')
        while self.model.associate('network', 'network'):
            pass
        while self.model.associate('network', 'vm_instance'):
            pass
        while self.model.associate('vm_instance', 'admin'):
            pass
        while self.model.associate('admin', 'principal'):
            pass
        self.model.print()
        self.model.plot()


if __name__ == "__main__":
    metamodel = {  'network': { 'abbreviation': 'N',
                                'n': {              'distribution': 'BinomialPlusOne', 
                                                    'n': 30, 
                                                    'p': 0.5}, 
                                'associated_assets': {
                                    'network': {    'distribution': 'Binomial', 
                                                    'n': 500, 
                                                    'p': 0.005}, 
                                    'vm_instance': {'distribution': 'Binomial', 
                                                    'n': 1000, 
                                                    'p': 0.005}}},
        'vm_instance': {        'abbreviation': 'VM',
                                'n': {              'distribution': 'Constant', 
                                                        'n': 100},
                                'associated_assets': {
                                    'network': {    'distribution': 'Constant', 
                                                    'n': 1},
                                    'admin': {      'distribution': 'Constant', 
                                                    'n': 1}}},
        'admin': {              'abbreviation': 'A',
                                'n': {              'distribution': 'Constant', 
                                                    'n': sys.maxsize},
                                'associated_assets': {
                                    'vm_instance': {'distribution': 'Constant', 
                                                    'n': 1},
                                    'principal': {  'distribution': 'BinomialPlusOne', 
                                                    'n': 5, 
                                                    'p': 0.1}}},
        'principal': {          'abbreviation': 'P',
                                'n': {              'distribution': 'BinomialPlusOne', 
                                                    'n': 100, 
                                                    'p': 0.05},
                                'associated_assets': {
                                    'admin': {  'distribution': 'Binomial', 
                                                'n': 200, 
                                                'p': 0.1}}}}
    sampler = Sampler(metamodel)
    sampler.sample()
