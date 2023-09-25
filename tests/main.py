import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../tests/examples'))
from example_metamodel import example_metamodel
from mal_sampler import Model

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
    plot_path = 'tests/plots/plot.png'
    model.plot(plot_path)
    model.print(summary=True)
    print(f'# Model plotted in {plot_path}.')
    print(f'# Comparing actual samples with targets.')
    model.compare_actual_samples_with_targets()