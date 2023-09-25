from src.probability_distribution import ProbabilityDistribution

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
