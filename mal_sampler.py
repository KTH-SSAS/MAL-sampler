from scipy.stats import binom
import random
import networkx as nx
import matplotlib.pyplot as plt
import sys


class ProbabilityDistribution:
    def __init__(self, distribution_dict: dict):
        self.distribution = distribution_dict['distribution']
        self.n = distribution_dict['n']
        if 'p' in distribution_dict:
            self.p = distribution_dict['p']

    def sample(self):
        if self.distribution == 'Binomial':
            return binom(n=self.n, p=self.p).rvs()
        elif self.distribution == 'Constant':
            return self.n
        elif self.distribution == 'BinomialPlusOne':
            return binom(n=self.n, p=self.p).rvs() + 1


class Asset:
    def __init__(self, name: str, asset_type_name: str, associated_assets_dict: dict):
        self.name = name
        self.asset_type_name = asset_type_name
        self.n_associated_assets = dict()
        self.associated_assets = dict()
        self.generation_completed = False
        for asset_name, dist_dict in associated_assets_dict.items():
            self.n_associated_assets[asset_name] = ProbabilityDistribution(
                dist_dict).sample()
            self.associated_assets[asset_name] = set()

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
                self.n_assets[asset_type] = ProbabilityDistribution(
                    self.metamodel[asset_type]['n']).sample()
            else:
                self.n_assets[asset_type] = sys.maxsize
            self.assets[asset_type] = set()

    def select_initial_asset_type(self):
        available_inital_asset_types = [a for a in list(
            self.metamodel.keys()) if 'n' in self.metamodel[a]]
        return random.choice(available_inital_asset_types)

    def all_assets(self):
        return [a for asset_type in self.assets for a in self.assets[asset_type]]

    def incompletely_associated_assets(self):
        return [a for a in self.all_assets() if not a.generation_completed]

    def available_targets(self, source_asset, target_asset_type):
        available_target_assets = [
            a for a in self.assets[target_asset_type] if a.accepts(source_asset.asset_type_name) and a not in source_asset.associated_assets[target_asset_type]]
        if target_asset_type == source_asset.asset_type_name:
            available_target_assets = [
                a for a in available_target_assets if a != source_asset]
        return available_target_assets

    def add(self, asset_type: str):
        if asset_type in self.metamodel:
            a = Asset(
                f"{self.metamodel[asset_type]['abbreviation']}{len(self.assets[asset_type])}", asset_type, self.metamodel[asset_type]['associated_assets'])
            self.assets[asset_type].add(a)
            return a
        else:
            raise ValueError(f'Unknown asset type: {asset_type}')

    def associate(self, source_asset, target_asset_type, source_asset_type, target_asset):
        source_asset.associated_assets[target_asset_type].add(
            target_asset)
        if source_asset_type not in target_asset.associated_assets:
            target_asset.associated_assets[source_asset_type] = set()
        target_asset.associated_assets[source_asset_type].add(
            source_asset)

    def complete_associations(self, source_asset: Asset):
        for target_asset_type in source_asset.n_associated_assets.keys():
            while source_asset.accepts(target_asset_type):
                target_asset = None
                available_target_assets = self.available_targets(
                    source_asset, target_asset_type)
                if len(available_target_assets) > 0:
                    target_asset = random.choice(available_target_assets)
                else:
                    if len(self.assets[target_asset_type]) < self.n_assets[target_asset_type]:
                        target_asset = self.add(target_asset_type)
                if target_asset:
                    self.associate(source_asset, target_asset_type,
                                   source_asset.asset_type_name, target_asset)
                else:
                    break
        source_asset.generation_completed = True

    def sample(self):
        initial_asset_type = self.select_initial_asset_type()
        asset = self.add(initial_asset_type)
        self.complete_associations(asset)
        while self.incompletely_associated_assets():
            asset = random.choice(self.incompletely_associated_assets())
            self.complete_associations(asset)

    def check_consistency(self):
        is_consistent = True
        for asset in self.all_assets():
            for associated_asset_type in asset.n_associated_assets.keys():
                if len(asset.associated_assets[associated_asset_type]) != asset.n_associated_assets[associated_asset_type]:
                    print(
                        f'Inconsistency: Asset {asset.name} has {len(asset.associated_assets[associated_asset_type])} associated {associated_asset_type} assets of {asset.n_associated_assets[associated_asset_type]} required associated assets.')
                    is_consistent = False
        return is_consistent

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

    model = Model(probably_self_contradictory_metamodel)
    model.sample()
    model.plot()
    model.check_consistency()
