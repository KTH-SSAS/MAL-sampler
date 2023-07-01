from constants import PLOT_FILE_NAME
from probability_distribution import ProbabilityDistribution
from example_metamodel import example_metamodel
from model import Model

if __name__ == "__main__":
    metamodel = example_metamodel(size_factor=10, size_constraining_asset_type='all')
    print(f'# Metamodel containing these assets: {[a for a in metamodel.keys()]}')
    model = Model(metamodel)
    model.sample()
    print(f'# Sampled a model containing {len(model.all_assets())} assets.')
    model.resolve_inconsistency()
    print(f'# After resolving inconsistencies, model contains {len(model.all_assets())} assets.')
    print(f'# Plotting.')
    model.plot(PLOT_FILE_NAME)
    model.print(summary=True)
    print(f'# Model plotted in {PLOT_FILE_NAME}.')
    print(f'# Comparing actual samples with targets.')
    model.compare_actual_samples_with_targets()