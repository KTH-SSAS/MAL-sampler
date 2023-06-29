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
        self.generation_completed = False

    def accepts(self, asset_type: str):
        if asset_type not in self.n_associated_assets:
            return False
        else:
            return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type]

    def print(self):
        print(
            f"{self.asset_type_name}: {self.name}. Associated assets: {[(n, [a.name for a in list(self.associated_assets[n])]) for n in self.associated_assets]}. Associated asset limits: {self.n_associated_assets}")


class Model:
    def __init__(self, metamodel: dict):
        self.n_assets = dict()
        self.assets = dict()
        self.metamodel = metamodel
        for asset_type in self.metamodel:
            if 'n' in self.metamodel[asset_type]:
                self.n_assets[asset_type] = self.sample_distribution(
                    self.metamodel[asset_type]['n'])
                print(
                    f'self.n_assets[{asset_type}]: n = {self.n_assets[asset_type]}.')
            else:
                self.n_assets[asset_type] = sys.maxsize
            self.assets[asset_type] = set()

    def all_assets(self):
        return [a for asset_type in self.assets for a in self.assets[asset_type]]

    def incomplete_assets(self):
        return [a for a in self.all_assets() if not a.generation_completed]

    def sample_distribution(self, distribution_dict: dict):
        if distribution_dict['distribution'] == 'Binomial':
            return binom(n=distribution_dict['n'], p=distribution_dict['p']).rvs()
        elif distribution_dict['distribution'] == 'Constant':
            return distribution_dict['n']
        elif distribution_dict['distribution'] == 'BinomialPlusOne':
            return binom(n=distribution_dict['n'], p=distribution_dict['p']).rvs() + 1

    def add(self, asset_type: str):
        print(f"  Attempting to add asset of type {asset_type}.")
        if len(self.assets[asset_type]) < self.n_assets[asset_type]:
            if asset_type in self.metamodel:
                abbreviation = self.metamodel[asset_type]['abbreviation']
                a = Asset(
                    f"{abbreviation}{len(self.assets[asset_type])}", asset_type)
                for asset_name, dist_dict in self.metamodel[asset_type]['associated_assets'].items():
                    a.n_associated_assets[asset_name] = self.sample_distribution(
                        dist_dict)
                    a.associated_assets[asset_name] = set()
                print('  Added ', end='')
                a.print()
            else:
                raise ValueError(f'Unknown asset type: {asset_type}')
            self.assets[asset_type].add(a)
            return a
        else:
            print(
                f'--Reached the limit of {self.n_assets[asset_type]} {asset_type} assets.')
            return None

    def associate(self, source_asset, target_asset_type, source_asset_type, target_asset):
        source_asset.associated_assets[target_asset_type].add(
                target_asset)
        if source_asset_type not in target_asset.associated_assets:
            target_asset.associated_assets[source_asset_type] = set()
        target_asset.associated_assets[source_asset_type].add(
                source_asset)

    def find_target_and_associate(self, source_asset: Asset, target_asset_type:str):
        print(f"  Finding target asset of type {target_asset_type} for source asset {source_asset.name}.")
        source_asset_type = source_asset.asset_type_name
        available_target_assets = [
            a for a in self.assets[target_asset_type] if a.accepts(source_asset_type)]
        available_target_assets = [
            a for a in available_target_assets if a not in source_asset.associated_assets[target_asset_type]]
        if target_asset_type == source_asset_type:
            available_target_assets = [
                a for a in available_target_assets if a != source_asset]
        if len(available_target_assets) > 0:
            target_asset = random.choice(available_target_assets)
            print(f"  Found target asset {target_asset.name}.")
        else:
            print(f"  Could not find target asset.")
            target_asset = self.add(target_asset_type)

        if target_asset:
            self.associate(source_asset, target_asset_type, source_asset_type, target_asset)
            return target_asset
        else:
            return None

    def select_initial_asset_type(self):
        available_inital_asset_types = [a for a in list(
            self.metamodel.keys()) if 'n' in self.metamodel[a]]
        return random.choice(available_inital_asset_types)

    def generate_associations_by_asset(self, asset: Asset):
        for associated_asset_type in asset.n_associated_assets.keys():
            while asset.n_associated_assets[associated_asset_type] > len(asset.associated_assets[associated_asset_type]):
                print(f'  {asset.name} has {len(asset.associated_assets[associated_asset_type])} associated {associated_asset_type} assets of {asset.n_associated_assets[associated_asset_type]} required associated assets.')
                print(f'  Generating association from {asset.name} to asset type {associated_asset_type} because it has {len(asset.associated_assets[associated_asset_type])} of {asset.n_associated_assets[associated_asset_type]} required associated assets.')
                target_asset = self.find_target_and_associate(asset, associated_asset_type)
                if not target_asset:
                    print(f'  Could not find target asset for {asset.name} to associate with. Aborting.')
                    asset.generation_completed = True
                    break
        asset.generation_completed = True

    def sample(self):
        initial_asset_type = self.select_initial_asset_type()
        print(f'Selected {initial_asset_type} as initial asset type.')
        asset = self.add(initial_asset_type)        
        print(f'Added {asset.name} as initial asset. Now generating associations.')
        self.generate_associations_by_asset(asset)
        while self.incomplete_assets():
            asset = random.choice(self.incomplete_assets())
            print(f'Now generating associations for {asset.asset_type_name} {asset.name}.')
            self.generate_associations_by_asset(asset)

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
        for asset_type_name in self.metamodel.keys():
            shape = self.metamodel[asset_type_name]['visualization']['shape']
            color = self.metamodel[asset_type_name]['visualization']['color']
            nx.draw_networkx_nodes(G, pos, nodelist=[nw.name for nw in self.assets[asset_type_name]],
                                   node_shape=shape, node_color=color, edgecolors='white', linewidths=0.5, node_size=50)

        nx.draw_networkx_edges(G, pos, edge_color='white', width=0.5)
        nx.draw_networkx_labels(G, pos, font_color='white', font_size=2)
        plt.axis('off')
        plt.savefig('model.png', dpi=1200, bbox_inches='tight',
                    pad_inches=0, facecolor='black')






if __name__ == "__main__":
    probably_self_contradictory_metamodel = {'network': {'abbreviation': 'N',
                                                         'n': {'distribution': 'BinomialPlusOne',
                                                               'n': 30,
                                                               'p': 0.5},
                                                         'associated_assets': {
                                                             'network': {'distribution': 'BinomialPlusOne',
                                                                         'n': 500,
                                                                         'p': 0.005},
                                                             'vm_instance': {'distribution': 'Binomial',
                                                                             'n': 1000,
                                                                             'p': 0.005}},
                                                         'visualization': {'shape': 's',
                                                                           'color': 'red'}},
                                             'vm_instance': {'abbreviation': 'VM',
                                                             'n': {'distribution': 'BinomialPlusOne',
                                                                   'n': 200,
                                                                   'p': 0.5},
                                                             'associated_assets': {
                                                                 'network': {'distribution': 'Constant',
                                                                             'n': 1},
                                                                 'admin_privileges': {'distribution': 'Constant',
                                                                                      'n': 1}},
                                                             'visualization': {'shape': 'o',
                                                                               'color': 'blue'}},
                                             'admin_privileges': {'abbreviation': 'A',
                                                                  'n': {'distribution': 'BinomialPlusOne',
                                                                        'n': 200,
                                                                        'p': 0.5},
                                                                  'associated_assets': {
                                                                      'vm_instance': {'distribution': 'Constant',
                                                                                      'n': 1},
                                                                      'principal': {'distribution': 'BinomialPlusOne',
                                                                                    'n': 5,
                                                                                    'p': 0.1}},
                                                                  'visualization': {'shape': 'v',
                                                                                    'color': 'yellow'}},
                                             'principal': {'abbreviation': 'P',
                                                           'n': {'distribution': 'BinomialPlusOne',
                                                                 'n': 100,
                                                                 'p': 0.05},
                                                           'associated_assets': {
                                                               'admin_privileges': {'distribution': 'Binomial',
                                                                                    'n': 200,
                                                                                    'p': 0.1}},
                                                           'visualization': {'shape': '^',
                                                                             'color': 'green'}}}

    minimally_specified_metamodel = {'network': {'abbreviation': 'N',
                                     'n': {'distribution': 'BinomialPlusOne',
                                           'n': 30,
                                           'p': 0.5},
                                     'associated_assets': {
                                         'network': {'distribution': 'BinomialPlusOne',
                                                     'n': 500,
                                                     'p': 0.005},
                                         'vm_instance': {'distribution': 'Binomial',
                                                         'n': 1000,
                                                         'p': 0.005}},
                                     'visualization': {'shape': 's',
                                                       'color': 'red'}},
                         'vm_instance': {'abbreviation': 'VM',
                                         'associated_assets': {
                                             'network': {'distribution': 'Constant',
                                                         'n': 1},
                                             'admin_privileges': {'distribution': 'Constant',
                                                                  'n': 1}},
                                         'visualization': {'shape': 'o',
                                                           'color': 'blue'}},
                         'admin_privileges': {'abbreviation': 'A',
                                              'associated_assets': {
                                                  'vm_instance': {'distribution': 'Constant',
                                                                  'n': 1},
                                                  'principal': {'distribution': 'BinomialPlusOne',
                                                                'n': 5,
                                                                'p': 0.1}},
                                              'visualization': {'shape': 'v',
                                                                'color': 'yellow'}},
                         'principal': {'abbreviation': 'P',
                                       'associated_assets': {
                                           'admin_privileges': {'distribution': 'Binomial',
                                                                'n': 200,
                                                                'p': 0.1}},
                                       'visualization': {'shape': '^',
                                                         'color': 'green'}}}

    minimal_constant_metamodel = {'network': {'abbreviation': 'N',
                                     'n': {'distribution': 'Constant',
                                           'n': 3},
                                     'associated_assets': {
                                         'network': {'distribution': 'Constant',
                                                     'n': 2},
                                         'vm_instance': {'distribution': 'Constant',
                                                         'n': 3}},
                                     'visualization': {'shape': 's',
                                                       'color': 'red'}},
                         'vm_instance': {'abbreviation': 'VM',
                                         'associated_assets': {
                                             'network': {'distribution': 'Constant',
                                                         'n': 1},
                                             'admin_privileges': {'distribution': 'Constant',
                                                                  'n': 1}},
                                         'visualization': {'shape': 'o',
                                                           'color': 'blue'}},
                         'admin_privileges': {'abbreviation': 'A',
                                              'associated_assets': {
                                                  'vm_instance': {'distribution': 'Constant',
                                                                  'n': 1},
                                                  'principal': {'distribution': 'Constant',
                                                                'n': 1}},
                                              'visualization': {'shape': 'v',
                                                                'color': 'yellow'}},
                         'principal': {'abbreviation': 'P',
                                       'associated_assets': {
                                           'admin_privileges': {'distribution': 'Constant',
                                                                'n': 2}},
                                       'visualization': {'shape': '^',
                                                         'color': 'green'}}}

    model = Model(minimal_constant_metamodel)
    model.sample()
    model.plot()


# Something is wrong. Each admin privilege should be associated with exactly one VM, but not all are.
