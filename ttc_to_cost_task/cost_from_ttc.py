import numpy as np
import re 

MAX_COST = 500.0

# Define the attack steps and their distributions
attack_steps = {
    "bypassSecurityAwareness": "VeryHardAndUncertain",
    "deliverMaliciousRemovableMedia": "Exponential(0.01)",
    "credentialTheft": "HardAndUncertain",
    "unsafeUserActivity": "Exponential(0.03)",
    "useLeakedCredentials": "EasyAndCertain",
    "guessCredentials": "HardAndUncertain",
    "inherentUserInteraction": "EasyAndUncertain",
    "exploitWithEffort": "Exponential(0.01)",
    "supplyChainAttack": "VeryHardAndUncertain",
    "bypassSupplyChainAuditing": "VeryHardAndUncertain",
    "bypassHardwareModificationsProtection": "VeryHardAndUncertain",
    "networkConnectFromResponse": "VeryHardAndUncertain",
    "bypassContainerization": "Exponential(0.1)",
    "attackerUnsafeUserActivityCapabilityWithoutReverseReach": "Exponential(0.01)",
    "bypassEffectiveness": "EasyAndUncertain",
    "bypassEavesdropDefenseFromPhysicalAccess": "Exponential(0.05)",
    "bypassAdversaryInTheMiddleDefenseFromPhysicalAccess": "Exponential(0.05)",
    "bypassAccessControl": "Exponential(0.05)",
    "bypassEavesdropDefense": "Exponential(0.05)",
    "bypassAdversaryInTheMiddleDefense": "Exponential(0.05)",
    "bypassRestricted": "Exponential(0.05)",
    "bypassPayloadInspection": "Exponential(0.05)"
}

# Define the number of samples
num_samples = 100

costs = {}

def process_sample(distribution):
    if 'Bernoulli' in distribution:
        prob = distribution['Bernoulli']
        scale = distribution['Exponential']
        scale = 1/scale
        sample = np.random.exponential(scale=scale) if np.random.choice([0, 1], p=[prob, 1 - prob]) else MAX_COST

    else:
        scale = distribution['Exponential']
        scale = 1/scale
        sample = np.random.exponential(scale=scale)

    return sample

# Generate samples and calculate cumulative values for each attack step
for attack_step, distribution in attack_steps.items():
    sum_of_samples = 0
    for _ in range(num_samples):
        if distribution == "EasyAndCertain":
            sample = process_sample({'Exponential': 1})
        elif distribution == "EasyAndUncertain":
            sample = process_sample({'Exponential': 1, 'Bernoulli': 0.5})
        elif distribution == "HardAndCertain":
            sample = process_sample({'Exponential': 0.1})
        elif distribution == "HardAndUncertain":
            sample = process_sample({'Exponential': 0.1, 'Bernoulli': 0.5})
        elif distribution == "VeryHardAndCertain":
            sample = process_sample({'Exponential': 0.01})
        elif distribution == "VeryHardAndUncertain":
            sample = process_sample({'Exponential': 0.01, 'Bernoulli': 0.5})
        else:
            if distribution.startswith("Exponential"):
                scale = float(distribution.split("(")[1].rstrip(")"))
                sample = process_sample({'Exponential': scale})
        
        sum_of_samples += sample
        cost = sum_of_samples / num_samples
        costs[attack_step] = cost


print("-"*100)
for attack_step, distribution in attack_steps.items():
    print(f"{attack_step}: {distribution}")
    if attack_step in costs:
        print(f"Cost for {attack_step}: {costs[attack_step]}")
    print("-"*100)
