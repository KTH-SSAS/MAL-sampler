import sys

from constants import PLOT_FILE_NAME
from probability_distribution import ProbabilityDistribution
from example_metamodel import example_metamodel
from model import Model

if __name__ == "__main__":
    metamodel = example_metamodel(size_factor=20, size_constraining_asset_type='network')
    print(f'# Metamodel containing these assets: {[a for a in metamodel.keys()]}')
    model = Model(metamodel)
    for asset_type in metamodel.keys():
        if model.n_assets[asset_type].value < sys.maxsize:
            print(f'# Size-constraining number of {asset_type} assets: {model.n_assets[asset_type].value}.')

    model.sample()
    print(f'# After resolving inconsistencies, model contains {len(model.all_assets())} assets.')
    print(f'# Plotting.')
    model.plot(PLOT_FILE_NAME)
    model.print(summary=True)
    print(f'# Model plotted in {PLOT_FILE_NAME}.')
    print(f'# Comparing actual samples with targets.')
    model.compare_actual_samples_with_targets()