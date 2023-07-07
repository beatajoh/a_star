import numpy as np

MAX_COST = 500.0

def parse_ttc(ttc):
    # Parse the TTC distribution
    if ttc['name'] == 'Exponential':
        arguments = ttc['arguments']
        if arguments:
            argument = arguments[0]
            return f"Exponential({argument})"
    else:
        return ttc['name']

def process_sample(distribution):
    # Generate a random sample for the given distribution
    if 'Bernoulli' in distribution:
        # Mixture of exponential and constant distribution
        prob = distribution['Bernoulli']
        scale = distribution['Exponential']
        scale = 1/scale
        sample = np.random.exponential(scale=scale) if np.random.choice([0, 1], p=[prob, 1 - prob]) else MAX_COST
    else:
        # Pure exponential distribution
        scale = distribution['Exponential']
        scale = 1/scale
        sample = np.random.exponential(scale=scale)
    return sample


def cost_from_ttc(ttc, num_samples=100):
    costs = {}

    # Parse the TTC distribution
    distribution = parse_ttc(ttc)

    sum_of_samples = 0
    for _ in range(num_samples):
        if distribution == "EasyAndCertain":
            # Generate sample for EasyAndCertain distribution
            sample = process_sample({'Exponential': 1})
        elif distribution == "EasyAndUncertain":
            # Generate sample for EasyAndUncertain distribution
            sample = process_sample({'Exponential': 1, 'Bernoulli': 0.5})
        elif distribution == "HardAndCertain":
            # Generate sample for HardAndCertain distribution
            sample = process_sample({'Exponential': 0.1})
        elif distribution == "HardAndUncertain":
            # Generate sample for HardAndUncertain distribution
            sample = process_sample({'Exponential': 0.1, 'Bernoulli': 0.5})
        elif distribution == "VeryHardAndCertain":
            # Generate sample for VeryHardAndCertain distribution
            sample = process_sample({'Exponential': 0.01})
        elif distribution == "VeryHardAndUncertain":
            # Generate sample for VeryHardAndUncertain distribution
            sample = process_sample({'Exponential': 0.01, 'Bernoulli': 0.5})
        else:
            if distribution.startswith("Exponential"):
                # Extract the scale value for custom Exponential distribution
                scale = float(distribution.split("(")[1].rstrip(")"))
                sample = process_sample({'Exponential': scale})
        sum_of_samples += sample

    cost = sum_of_samples / num_samples

    return cost



# Example TTC inputs
ttc1 = {
    "type": "function",
    "name": "Exponential",
    "arguments": [0.1]
}

ttc2 = {
    "type": "function",
    "name": "EasyAndCertain",
    "arguments": []
}

ttc3 = {
    "type": "function",
    "name": "EasyAndUncertain",
    "arguments": []
}

ttc4 = {
    "type": "function",
    "name": "HardAndCertain",
    "arguments": []
}

ttc5 = {
    "type": "function",
    "name": "HardAndUncertain",
    "arguments": []
}

ttc6 = {
    "type": "function",
    "name": "VeryHardAndCertain",
    "arguments": []
}

ttc7 = {
    "type": "function",
    "name": "VeryHardAndUncertain",
    "arguments": []
}


distribution1 = parse_ttc(ttc1)
distribution2 = parse_ttc(ttc2)
distribution3 = parse_ttc(ttc3)
distribution4 = parse_ttc(ttc4)
distribution5 = parse_ttc(ttc5)
distribution6 = parse_ttc(ttc6)
distribution7 = parse_ttc(ttc7)

costs1 = cost_from_ttc(distribution1)
costs2 = cost_from_ttc(distribution2)
costs3 = cost_from_ttc(distribution3)
costs4 = cost_from_ttc(distribution4)
costs5 = cost_from_ttc(distribution5)
costs6 = cost_from_ttc(distribution6)
costs7 = cost_from_ttc(distribution7)

rounded_cost1 = int(round(costs1, 0))
rounded_cost2 = int(round(costs2, 0))
rounded_cost3 = int(round(costs3, 0))
rounded_cost4 = int(round(costs4, 0))
rounded_cost5 = int(round(costs5, 0))
rounded_cost6 = int(round(costs6, 0))
rounded_cost7 = int(round(costs7, 0))

print(f"Cost for {distribution1}: {rounded_cost1}")
print(f"Cost for {distribution2}: {rounded_cost2}")
print(f"Cost for {distribution3}: {rounded_cost3}")
print(f"Cost for {distribution4}: {rounded_cost4}")
print(f"Cost for {distribution5}: {rounded_cost5}")
print(f"Cost for {distribution6}: {rounded_cost6}")
print(f"Cost for {distribution7}: {rounded_cost7}")