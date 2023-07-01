import random
import networkx as nx
import matplotlib.pyplot as plt
import sys
from constants import N_SAMPLES_FOR_BOUNDS, N_INCONSISTENCY_RESOLUTION_ATTEMPTS
from probability_distribution import ProbabilityDistribution
from asset import Asset

'''
The Model class is used to manage the overall structure of assets in the system. 
It includes functions to add and remove assets, associate assets, and generate a random model.
'''
class Model:
    def __init__(self, metamodel: dict):
        '''
        Initialize a Model instance.
        metamodel : A dictionary that represents the metamodel used to generate the assets.
        '''
        self.n_assets = dict()
        self.assets = dict()
        self.metamodel = metamodel
        for asset_type in self.metamodel:
            if 'n' in self.metamodel[asset_type]:
                self.n_assets[asset_type] = ProbabilityDistribution(
                    self.metamodel[asset_type]['n'], N_SAMPLES_FOR_BOUNDS)
            else:
                self.n_assets[asset_type] = ProbabilityDistribution(
                    {'distribution': 'Constant', 'n': sys.maxsize}, N_SAMPLES_FOR_BOUNDS)
            self.assets[asset_type] = set()

    def select_initial_asset_type(self):
        '''
        Select the initial asset type to be added to the model.
        '''
        available_inital_asset_types = [a for a in list(
            self.metamodel.keys())]
        return random.choice(available_inital_asset_types)

    def all_assets(self):
        '''
        Get a list of all assets in the model.
        '''
        return [a for asset_type in self.assets for a in self.assets[asset_type]]

    def incompletely_associated_assets(self):
        '''
        Get a list of all assets that have not completed their association process.
        '''
        return [a for a in self.all_assets() if not a.generation_completed]

    def available_targets(self, source_asset, target_asset_type, force_associate=False):
        '''
        Get a list of available targets for a source asset.
        source_asset : The source asset that is looking for potential targets to associate with.
        target_asset_type : The type of the potential targets.
        force_associate : A flag that, if set to True, uses the upper limit of the number of associations instead of the current value.
        '''
        available_target_assets = [
            a for a in self.assets[target_asset_type] if a.accepts(source_asset.asset_type_name, force_accept=force_associate) and a not in source_asset.associated_assets[target_asset_type]]
        if target_asset_type == source_asset.asset_type_name:
            available_target_assets = [
                a for a in available_target_assets if a != source_asset]
        return available_target_assets

    def add(self, asset_type: str):
        '''
        Add an asset of a specified type to the model.
        asset_type : The type of the asset to be added.
        '''
        if asset_type in self.metamodel:
            a = Asset(
                f"{self.metamodel[asset_type]['abbreviation']}{len(self.assets[asset_type])}", asset_type, self.metamodel[asset_type]['associated_assets'])
            self.assets[asset_type].add(a)
            return a
        else:
            raise ValueError(f'Unknown asset type: {asset_type}')

    def remove(self, asset: Asset):
        '''
        Remove an asset from the model.
        asset : The asset to be removed.
        '''
        asset.disassociate_all()
        if asset in self.assets[asset.asset_type_name]:
            self.assets[asset.asset_type_name].remove(asset)

    def complete_associations(self, source_asset: Asset, force_associate=False):
        '''
        Complete the associations of a source asset.
        source_asset : The source asset that needs to complete its associations.
        force_associate : A flag that, if set to True, forces the association process to its upper limit.
        '''
        for target_asset_type in source_asset.n_associated_assets.keys():
            while source_asset.accepts(target_asset_type):
                target_asset = None
                available_target_assets = self.available_targets(
                    source_asset, target_asset_type, force_associate=force_associate)
                if len(available_target_assets) > 0:
                    target_asset = random.choice(available_target_assets)
                else:
                    if len(self.assets[target_asset_type]) < self.n_assets[target_asset_type].value:
                        if not force_associate:
                            target_asset = self.add(target_asset_type)
                if target_asset:
                    source_asset.associate(target_asset)
                else:
                    break
        source_asset.generation_completed = True

    def sample(self):
        '''
        Generate a random model based on the specified metamodel.
        '''
        initial_asset_type = self.select_initial_asset_type()
        print(f'# Initial asset type: {initial_asset_type}')
        asset = self.add(initial_asset_type)
        self.complete_associations(asset)
        while self.incompletely_associated_assets():
            asset = random.choice(self.incompletely_associated_assets())
            self.complete_associations(asset)
            print(f'\r# Number of assets: {len(self.all_assets())}. Number of incomplete assets: {len(self.incompletely_associated_assets())}. Latest: {asset.asset_type_name} {asset.name}                         ', end='')
        print()

    def check_consistency(self):
        '''
        Check the consistency of the model. Inconsistent assets are those that have less or more associations than the specified limits.
        '''
        inconsistent = []
        for asset in self.all_assets():
            for associated_asset_type in asset.n_associated_assets.keys():
                if len(asset.associated_assets[associated_asset_type]) < asset.n_associated_assets[associated_asset_type].low or len(asset.associated_assets[associated_asset_type]) > asset.n_associated_assets[associated_asset_type].high:
                    inconsistent.append(asset)
        return inconsistent

    def resolve_inconsistency(self):
        '''
        Resolve any inconsistencies in the model. It tries to resolve inconsistencies up to N_INCONSISTENCY_RESOLUTION_ATTEMPTS times before giving up.
        '''
        inconsistent_assets = self.check_consistency()
        counter = 0
        while inconsistent_assets:
            counter += 1
            for inconsistent_asset in inconsistent_assets:
                self.complete_associations(
                    inconsistent_asset, force_associate=True)
            inconsistent_assets = self.check_consistency()
            for inconsistent_asset in inconsistent_assets:
                self.remove(inconsistent_asset)
            inconsistent_assets = self.check_consistency()
            if counter > N_INCONSISTENCY_RESOLUTION_ATTEMPTS:
                print(f'Failed to resolve inconsistencies in {N_INCONSISTENCY_RESOLUTION_ATTEMPTS} iterations.')
                break

    def compare_actual_samples_with_targets(self):
        '''
        Compare the actual number of each type of asset and their associations with the target values.
        '''
        for asset_type in self.metamodel:
            if 'n' in self.metamodel[asset_type]:
                if len(self.assets[asset_type]) == self.n_assets[asset_type].value:
                    print(f'# + The number of generated {asset_type} assets corresponds precisely to the sampled value.')
                else:
                    if len(self.assets[asset_type]) < self.n_assets[asset_type].low:
                        print(f'# - The number of generated {asset_type} assets ({len(self.assets[asset_type])}) is lower than the lower bound ({self.n_assets[asset_type].low}) and thus way out of distribution.')
                    elif len(self.assets[asset_type]) > self.n_assets[asset_type].high:
                        print(f'# - The number of generated {asset_type} assets ({len(self.assets[asset_type])}) is higher than the upper bound ({self.n_assets[asset_type].high}) and thus way out of distribution.')
                    else:
                        print(f'# + The number of generated {asset_type} assets ({len(self.assets[asset_type])}) does not correspond perfectly to sampled targets but is in distribution.')
            mismatch = False
            n_associated_mismatch_dict = dict()
            n_out_of_distribution_associated_mismatch_dict = dict()
            for associated_asset_type in self.metamodel[asset_type]['associated_assets']:
                if associated_asset_type not in n_associated_mismatch_dict:
                    n_associated_mismatch_dict[associated_asset_type] = 0
                    n_out_of_distribution_associated_mismatch_dict[associated_asset_type] = 0
                for asset in self.assets[asset_type]:
                    if len(asset.associated_assets[associated_asset_type]) != asset.n_associated_assets[associated_asset_type].value:
                        mismatch = True
                        n_associated_mismatch_dict[associated_asset_type] += 1
                        if len(asset.associated_assets[associated_asset_type]) < asset.n_associated_assets[associated_asset_type].low:
                            n_out_of_distribution_associated_mismatch_dict[associated_asset_type] += 1
                        elif len(asset.associated_assets[associated_asset_type]) > asset.n_associated_assets[associated_asset_type].high:
                            n_out_of_distribution_associated_mismatch_dict[associated_asset_type] += 1
                if n_associated_mismatch_dict[associated_asset_type] > 0:
                    if n_out_of_distribution_associated_mismatch_dict[associated_asset_type] == 0:
                        print(f'# - For the {len(self.assets[asset_type])} {asset_type} assets\' {associated_asset_type} associations, a total of {n_associated_mismatch_dict[associated_asset_type]} failed to perfectly meet the sampled target, but remained within distribution.')
                    else:
                        print(f'# - For the {len(self.assets[asset_type])} {asset_type} assets\' {associated_asset_type} associations, a total of {n_associated_mismatch_dict[associated_asset_type]} failed to perfectly meet the sampled target and a {n_out_of_distribution_associated_mismatch_dict[associated_asset_type]} were out of distribution.')
            if not mismatch:
                print(f'# + The number of associated assets for {asset_type} corresponds precisely to the sampled value.')
            print('If results are far from targets, the metamodel probability distributions might be inconsistently specified.')

    def print(self, summary=True):
        '''
        Print the details of the model.
        summary : If set to True, it prints only a summary of the model. Otherwise, it prints the details of each asset.
        '''
        for asset_type in self.assets.keys():
            if summary:
                print(f'# {asset_type}: {len(self.assets[asset_type])}')
            else:
                print(f'# {asset_type}:')
                for asset in self.assets[asset_type]:
                    asset.print()

    def plot(self, filename: str):
        '''
        Plot the model using networkx and matplotlib.
        filename : The filename to save the plot.
        '''
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
