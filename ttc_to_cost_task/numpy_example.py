import numpy as np


# Bernoulli
p = 0.3
bernoulli_sample = np.random.choice([0, 1], p=[1 - p, p])
print("Bernoulli sample:", bernoulli_sample)

# Binomial
n = 10
p = 0.5
binomial_sample = np.random.binomial(n, p)
print("Binomial sample:", binomial_sample)

# Exponential
lambda_val = 0.5
exponential_sample = np.random.exponential(scale=1 / lambda_val)
print("Exponential sample:", exponential_sample)

# Gamma
k = 2
theta = 3
gamma_sample = np.random.gamma(k, theta)
print("Gamma sample:", gamma_sample)

# LogNormal
mu = 1
sigma = 0.5
lognormal_sample = np.random.lognormal(mean=mu, sigma=sigma)
print("LogNormal sample:", lognormal_sample)

# Pareto
m = 1
alpha = 2
pareto_sample = np.random.pareto(alpha) + m
print("Pareto sample:", pareto_sample)

# TruncatedNormal
mu = 5
sigma = 2
truncated_normal_sample = np.random.normal(mu, sigma)
truncated_normal_sample = np.clip(truncated_normal_sample, mu - 2 * sigma, mu + 2 * sigma)
print("TruncatedNormal sample:", truncated_normal_sample)

# Uniform
min_val = 0
max_val = 10
uniform_sample = np.random.uniform(min_val, max_val)
print("Uniform sample:", uniform_sample)

# Ordinal distributions
easy_and_certain_sample = np.random.exponential(scale=1)
easy_and_uncertain_sample = np.random.choice([0, 1], p=[0.5, 0.5])
hard_and_certain_sample = np.random.exponential(scale=0.1)
hard_and_uncertain_sample = np.random.choice([0, 1], p=[0.5, 0.5]) * np.random.exponential(scale=0.1)
very_hard_and_certain_sample = np.random.exponential(scale=0.01)
very_hard_and_uncertain_sample = np.random.choice([0, 1], p=[0.5, 0.5]) * np.random.exponential(scale=0.01)

print("EasyAndCertain sample:", easy_and_certain_sample)
print("EasyAndUncertain sample:", easy_and_uncertain_sample)
print("HardAndCertain sample:", hard_and_certain_sample)
print("HardAndUncertain sample:", hard_and_uncertain_sample)
print("VeryHardAndCertain sample:", very_hard_and_certain_sample)
print("VeryHardAndUncertain sample:", very_hard_and_uncertain_sample)
