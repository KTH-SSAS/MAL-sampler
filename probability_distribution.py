from scipy.stats import binom
from constants import N_SAMPLES_FOR_BOUNDS

'''
The ProbabilityDistribution class is used to represent a probability distribution. 
It supports three types of distribution: 'Binomial', 'Constant', and 'BinomialPlusOne'.
'''
class ProbabilityDistribution:
    def __init__(self, distribution_dict: dict, n_samples_for_bounds: int = N_SAMPLES_FOR_BOUNDS):
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
