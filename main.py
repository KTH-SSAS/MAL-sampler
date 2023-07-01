from constants import PLOT_FILE_NAME
from probability_distribution import ProbabilityDistribution
from example_metamodel import example_metamodel
from model import Model

if __name__ == "__main__":
    metamodel = example_metamodel(size_factor=20, initial_asset_type='network')
    print(f'# Metamodel containing these assets: {[a for a in metamodel.keys()]}')
    model = Model(metamodel)
    model.sample()
    print(f'# Sampled a model containing {len(model.all_assets())} assets.')
    model.resolve_inconsistency()
    print(f'# After resolving inconsistencies, model contains {len(model.all_assets())} assets.')
    model.plot(PLOT_FILE_NAME)
    print(f'# Model plotted in {PLOT_FILE_NAME}.')
    model.compare_actual_samples_with_targets()