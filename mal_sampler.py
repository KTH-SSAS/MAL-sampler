from scipy.stats import binom
import random
import networkx as nx
import matplotlib.pyplot as plt
import sys


class ProbabilityDistribution:
    def __init__(self, distribution_dict: dict, n_samples_for_bounds: int = 100):
        self.distribution = distribution_dict['distribution']
        self.n = distribution_dict['n']
        if 'p' in distribution_dict:
            self.p = distribution_dict['p']
        samples = [self.sample() for _ in range(n_samples_for_bounds)]
        sorted_samples = sorted(samples)
        self.value = samples[0]
        self.low = sorted_samples[0]
        self.high = sorted_samples[-1]

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
                dist_dict)
            self.associated_assets[asset_name] = set()

    def accepts(self, asset_type: str, force_accept=False):
        if asset_type not in self.n_associated_assets:
            return False
        else:
            if not force_accept:
                return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type].value
            else:
                return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type].high

    def associate(self, target):
        self.associated_assets[target.asset_type_name].add(target)
        if self.asset_type_name not in target.associated_assets:
            target.associated_assets[self.asset_type_name] = set()
        target.associated_assets[self.asset_type_name].add(self)

    def disassociate(self, target):
        self.associated_assets[target.asset_type_name].remove(target)
        target.associated_assets[self.asset_type_name].remove(self)

    def disassociate_all(self):
        for asset_type in self.associated_assets:
            for target in self.associated_assets[asset_type]:
                target.associated_assets[self.asset_type_name].remove(self)
        self.associated_assets = dict()

    def print(self):
        print(
            f"{self.asset_type_name}: {self.name}. Associated assets: {[(n, [a.name for a in list(self.associated_assets[n])]) for n in self.associated_assets]}. Associated asset limits: {[n.value for n in self.n_associated_assets]}")


class Model:
    def __init__(self, metamodel: dict):
        self.n_assets = dict()
        self.assets = dict()
        self.metamodel = metamodel
        for asset_type in self.metamodel:
            if 'n' in self.metamodel[asset_type]:
                self.n_assets[asset_type] = ProbabilityDistribution(self.metamodel[asset_type]['n'])
            else:
                self.n_assets[asset_type] = ProbabilityDistribution({'distribution': 'Constant', 'n': sys.maxsize})
            self.assets[asset_type] = set()

    def select_initial_asset_type(self):
        available_inital_asset_types = [a for a in list(
            self.metamodel.keys()) if 'n' in self.metamodel[a]]
        return random.choice(available_inital_asset_types)

    def all_assets(self):
        return [a for asset_type in self.assets for a in self.assets[asset_type]]

    def incompletely_associated_assets(self):
        return [a for a in self.all_assets() if not a.generation_completed]

    def available_targets(self, source_asset, target_asset_type, force_associate=False):
        available_target_assets = [
            a for a in self.assets[target_asset_type] if a.accepts(source_asset.asset_type_name, force_accept=force_associate) and a not in source_asset.associated_assets[target_asset_type]]
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

    def remove(self, asset: Asset):
        asset.disassociate_all()
        if asset in self.assets[asset.asset_type_name]:
            self.assets[asset.asset_type_name].remove(asset)

    def complete_associations(self, source_asset: Asset, force_associate=False):
        for target_asset_type in source_asset.n_associated_assets.keys():
            while source_asset.accepts(target_asset_type):
                target_asset = None
                available_target_assets = self.available_targets(
                    source_asset, target_asset_type, force_associate=force_associate)
                if len(available_target_assets) > 0:
                    target_asset = random.choice(available_target_assets)
                    if force_associate:
                        print(f'Forced association between {source_asset.asset_type_name} {source_asset.name} and {target_asset.asset_type_name} {target_asset.name}')
                else:
                    if len(self.assets[target_asset_type]) < self.n_assets[target_asset_type].value:
                        target_asset = self.add(target_asset_type)
                        if force_associate:
                            print(f'Forced creation of new asset of type {target_asset_type}')
                if target_asset:
                    source_asset.associate(target_asset)
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
        inconsistent_assets = []
        for asset in self.all_assets():
            for associated_asset_type in asset.n_associated_assets.keys():
                if len(asset.associated_assets[associated_asset_type]) < asset.n_associated_assets[associated_asset_type].low or len(asset.associated_assets[associated_asset_type]) > asset.n_associated_assets[associated_asset_type].high:
                    inconsistent_assets.append(asset)
                    print(f'Inconsistent asset: {asset.name} ({asset.asset_type_name}): {len(asset.associated_assets[associated_asset_type])} associated {associated_asset_type} assets, targeted  {asset.n_associated_assets[associated_asset_type].value} and accepts between {asset.n_associated_assets[associated_asset_type].low} and {asset.n_associated_assets[associated_asset_type].high}')
        return inconsistent_assets

    def print(self):
        for asset_type in self.assets.keys():
            for asset in self.assets[asset_type]:
                asset.print()

    def plot(self, filename: str):
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
        plt.savefig(filename, dpi=1200, bbox_inches='tight',
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

    minimal_probabilistic_metamodel = {'network': {'abbreviation': 'N',
                                              'n': {'distribution': 'BinomialPlusOne',
                                                    'n': 3,
                                                    'p': 0.5},
                                              'associated_assets': {
                                                  'network': {'distribution': 'BinomialPlusOne',
                                                              'n': 2,
                                                              'p': 0.5},
                                                  'vm_instance': {'distribution': 'BinomialPlusOne',
                                                                  'n': 30,
                                                                  'p': 0.05}},
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
                                                                         'n': 3,
                                                                         'p': 0.5}},
                                                       'visualization': {'shape': 'v',
                                                                         'color': 'yellow'}},
                                  'principal': {'abbreviation': 'P',
                                                'associated_assets': {
                                                    'admin_privileges': {'distribution': 'BinomialPlusOne',
                                                                         'n': 3,
                                                                         'p': 0.5}},
                                                'visualization': {'shape': '^',
                                                                  'color': 'green'}}}


    model = Model(probably_self_contradictory_metamodel)
    model.sample()
    inconsistent_assets = model.check_consistency()
    print(f'Assets: {len(model.all_assets())}.')
    print(f'Inconsistent assets: {len(inconsistent_assets)}')
    model.plot('model_1.png')
    counter = 0
    while inconsistent_assets:
        counter += 1
        for inconsistent_asset in inconsistent_assets:
            print(f'Attempting to force association for {inconsistent_asset.name}.')
            model.complete_associations(inconsistent_asset, force_associate=True)
        inconsistent_assets = model.check_consistency()
        print(f'Remaining inconsistent assets: {len(inconsistent_assets)}')
        model.plot('model_2.png')
        for inconsistent_asset in inconsistent_assets:
            model.remove(inconsistent_asset)
        print(f'Removed {inconsistent_asset.name} from the model. Remaining assets: {len(model.all_assets())}.')
        inconsistent_assets = model.check_consistency()
        print(f'Remaining inconsistent assets: {len(inconsistent_assets)}')
        model.plot('model_3.png')
        if counter > 10:
            break

