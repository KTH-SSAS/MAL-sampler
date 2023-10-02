import random
import sys
import matplotlib.pyplot as plt
import networkx as nx
from scipy.stats import binom

'''
The ProbabilityDistribution class is used to represent a probability distribution. 
It supports three types of distribution: 'Binomial', 'Constant', and 'BinomialPlusOne'.
'''
class ProbabilityDistribution:
    def __init__(self, distribution_dict: dict, n_samples_for_bounds: int = 100):
        '''
        Initialize a ProbabilityDistribution instance.
        distribution_dict : A dictionary that contains the type of distribution and the necessary parameters.
        n_samples_for_bounds : The number of samples used to calculate the low and high bounds of the distribution.
        '''
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
        '''
        Generate a sample based on the specified distribution and parameters.
        '''
        if self.distribution == 'Binomial':
            return binom(n=self.n, p=self.p).rvs()
        elif self.distribution == 'Constant':
            return self.n
        elif self.distribution == 'BinomialPlusOne':
            return binom(n=self.n, p=self.p).rvs() + 1


'''
The Asset class represents an individual asset in the system.
Each asset has a name, type, and relationships (associations) with other assets.
'''
class Asset:
    def __init__(self, name: str, asset_type_name: str, associated_assets_dict: dict):
        '''
        Initialize an Asset instance.
        name : The name of the asset.
        asset_type_name : The type of the asset.
        associated_assets_dict : A dictionary that represents the associated assets and their respective distributions.
        '''
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
        '''
        Check if the asset can accept more associations of a given type.
        asset_type : The type of the potential association.
        force_accept : A flag that, if set to True, uses the upper limit of the number of associations instead of the current value.
        '''
        if asset_type not in self.n_associated_assets:
            return False
        else:
            if not force_accept:
                return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type].value
            else:
                return len(self.associated_assets[asset_type]) < self.n_associated_assets[asset_type].high

    def associate(self, target):
        '''
        Create an association between the asset and a target asset.
        target : The target asset to associate with.
        '''
        self.associated_assets[target.asset_type_name].add(target)
        if self.asset_type_name not in target.associated_assets:
            target.associated_assets[self.asset_type_name] = set()
        target.associated_assets[self.asset_type_name].add(self)

    def disassociate(self, target):
        '''
        Remove an association between the asset and a target asset.
        target : The target asset to disassociate from.
        '''
        self.associated_assets[target.asset_type_name].remove(target)
        target.associated_assets[self.asset_type_name].remove(self)

    def disassociate_all(self):
        '''
        Remove all associations of the asset.
        '''
        for asset_type in self.associated_assets:
            for target in self.associated_assets[asset_type]:
                target.associated_assets[self.asset_type_name].remove(self)
        self.associated_assets = dict()

    def print(self):
        '''
        Print the details of the asset, its associations, and the limits of each association.
        '''
        print(
            f"{self.asset_type_name}: {self.name}. Associated assets: {[(n, [a.name for a in list(self.associated_assets[n])]) for n in self.associated_assets]}. Associated asset limits: {[n.value for n in self.n_associated_assets]}")


'''
The Model class is used to manage the overall structure of assets in the system. 
It includes functions to add and remove assets, associate assets, and generate a random model.
'''
class Model:
    def __init__(self, metamodel: dict, n_consistency_resolution_attempts=10, n_samples_for_bounds=100):
        '''
        Initialize a Model instance.
        metamodel : A dictionary that represents the metamodel used to generate the assets.
        '''
        self.n_assets = dict()
        self.assets = dict()
        self.metamodel = metamodel
        self.n_consistency_resolution_attempts = n_consistency_resolution_attempts
        self.n_samples_for_bounds = n_samples_for_bounds
        for asset_type in self.metamodel:
            if 'n' in self.metamodel[asset_type]:
                self.n_assets[asset_type] = ProbabilityDistribution(
                    self.metamodel[asset_type]['n'], self.n_samples_for_bounds)
            else:
                self.n_assets[asset_type] = ProbabilityDistribution(
                    {'distribution': 'Constant', 'n': sys.maxsize}, self.n_samples_for_bounds)
            self.assets[asset_type] = set()

    def __select_initial_asset_type(self):
        '''
        Select the initial asset type to be added to the model.
        '''
        available_inital_asset_types = [a for a in list(
            self.metamodel.keys())]
        return random.choice(available_inital_asset_types)

    def __all_assets(self):
        '''
        Get a list of all assets in the model.
        '''
        return [a for asset_type in self.assets for a in self.assets[asset_type]]

    def __incompletely_associated_assets(self):
        '''
        Get a list of all assets that have not completed their association process.
        '''
        return [a for a in self.__all_assets() if not a.generation_completed]

    def __available_targets(self, source_asset, target_asset_type, force_associate=False):
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

    def __add(self, asset_type: str):
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

    def __remove(self, asset: Asset):
        '''
        Remove an asset from the model.
        asset : The asset to be removed.
        '''
        asset.disassociate_all()
        if asset in self.assets[asset.asset_type_name]:
            self.assets[asset.asset_type_name].remove(asset)

    def __complete_associations(self, source_asset: Asset, force_associate=False):
        '''
        Complete the associations of a source asset.
        source_asset : The source asset that needs to complete its associations.
        force_associate : A flag that, if set to True, forces the association process to its upper limit.
        '''
        for target_asset_type in source_asset.n_associated_assets.keys():
            while source_asset.accepts(target_asset_type):
                target_asset = None
                available_target_assets = self.__available_targets(
                    source_asset, target_asset_type, force_associate=force_associate)
                if len(available_target_assets) > 0:
                    target_asset = random.choice(available_target_assets)
                else:
                    if len(self.assets[target_asset_type]) < self.n_assets[target_asset_type].value:
                        if not force_associate:
                            target_asset = self.__add(target_asset_type)
                if target_asset:
                    source_asset.associate(target_asset)
                else:
                    break
        source_asset.generation_completed = True

    def __sample_tentatively(self):
        '''
        Generate a random model based on the specified metamodel.
        '''
        initial_asset_type = self.__select_initial_asset_type()
        print(f'# Initial asset type: {initial_asset_type}')
        asset = self.__add(initial_asset_type)
        self.__complete_associations(asset)
        while self.__incompletely_associated_assets():
            asset = random.choice(self.__incompletely_associated_assets())
            self.__complete_associations(asset)
            print(f'\r# Number of assets: {len(self.__all_assets())}. Number of incomplete assets: {len(self.__incompletely_associated_assets())}. Latest: {asset.asset_type_name} {asset.name}                         ', end='')
        print()

    def __check_consistency(self):
        '''
        Check the consistency of the model. Inconsistent assets are those that have less or more associations than the specified limits.
        '''
        inconsistent = []
        for asset in self.__all_assets():
            for associated_asset_type in asset.n_associated_assets.keys():
                if len(asset.associated_assets[associated_asset_type]) < asset.n_associated_assets[associated_asset_type].low or len(asset.associated_assets[associated_asset_type]) > asset.n_associated_assets[associated_asset_type].high:
                    inconsistent.append(asset)
        return inconsistent

    def __resolve_inconsistency(self):
        '''
        Resolve any inconsistencies in the model. It tries to resolve inconsistencies up to N_INCONSISTENCY_RESOLUTION_ATTEMPTS times before giving up.
        '''
        inconsistent_assets = self.__check_consistency()
        counter = 0
        while inconsistent_assets:
            counter += 1
            for inconsistent_asset in inconsistent_assets:
                self.__complete_associations(
                    inconsistent_asset, force_associate=True)
            inconsistent_assets = self.__check_consistency()
            for inconsistent_asset in inconsistent_assets:
                self.__remove(inconsistent_asset)
            inconsistent_assets = self.__check_consistency()
            if counter > self.n_consistency_resolution_attempts:
                print(f'Failed to resolve inconsistencies in {self.n_consistency_resolution_attempts} iterations.')
                break

    def sample(self):
        '''
        Generate a random model based on the specified metamodel. It tries to resolve inconsistencies up to N_INCONSISTENCY_RESOLUTION_ATTEMPTS times before giving up.
        '''
        self.__sample_tentatively()
        print(f'# Sampled a model containing {len(self.__all_assets())} assets.')
        self.__resolve_inconsistency()
        print(f'# After resolving inconsistencies, model contains {len(self.__all_assets())} assets.')

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
