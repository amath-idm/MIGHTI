"""
Script to plot age-dependent HIV prevalence without interactions
"""

# Imports
import starsim as ss
import pylab as pl
import pandas as pd
import numpy as np
import sciris as sc

beta = 0
if beta==0: print('Warning: transmission turned off!')

# Create the networks - sexual and maternal
mf = ss.MFNet(
    duration=1/24,  # Mean duration of relationships
    acts=80,
)
maternal = ss.MaternalNet()
networks = [mf, maternal]

# Create demographics
fertility_rates = {'fertility_rate': pd.read_csv(sc.thispath() / 'tests/test_data/nigeria_asfr.csv')}
pregnancy = ss.Pregnancy(pars=fertility_rates)
death_rates = {'death_rate': pd.read_csv(sc.thispath() / 'tests/test_data/nigeria_deaths.csv'), 'units': 1}
death = ss.Deaths(death_rates)

age_data = {
    0: 0,
    15: 0.056,
    20: 0.172,
    25: 0.303,
    30: 0.425,
    35: 0.525,
    40: 0.572,
    45: 0.501,
    50: 0.435,
    55: 0.338,
    60: 0.21,
    65: 0.147,
    99: 0,
}
n_age_bins = len(age_data) - 1
age_bins = list(age_data.keys())
left_bins = age_bins[:-1]
right_bins = age_bins[1:]
left_right = list(zip(left_bins, right_bins))
age_vals = list(age_data.values())

# Define age-dependent initial prevalence function
def age_dependent_prevalence(module=None, sim=None, size=None):
    ages = sim.people.age[size]  # Initial ages of agents
    prevalence = np.zeros(len(ages))
    
    for i in range(n_age_bins):
        left = age_bins[i]
        right = age_bins[i+1]
        value = age_vals[i]
        prevalence[(ages >= left) & (ages < right)] = value

    return prevalence

# Initialize HIV with age-dependent initial prevalence
hiv = ss.HIV(
    init_prev = ss.bernoulli(age_dependent_prevalence),
    beta = beta, # Overall transmission rate
)

# Run baseline HIV simulation without interactions
print('Running baseline HIV simulation without interactions')
baseline_sim = ss.Sim(
    n_agents=500000,
    networks=networks,
    diseases=[hiv],
    start=2021,
    end=2022
)
baseline_sim.run()


# Calculate and plot HIV prevalence by age group
age_group_labels = [f'{left}-{right-1}' for left,right in left_right]
age_results = {label: np.zeros(len(baseline_sim.yearvec)) for label in age_group_labels}
population_by_age_group = {label: np.zeros(len(baseline_sim.yearvec)) for label in age_group_labels}

# Check initial prevalence
initial_prevalence = {}
for (start, end), label in zip(left_right, age_group_labels):
    # Create a mask for agents in the current age group
    age_mask = (baseline_sim.people.age >= start) & (baseline_sim.people.age < end)
    # Count total population in this age group
    population_in_group = np.sum(age_mask)
    # Count infected population in this age group
    infected_in_group = np.sum(baseline_sim.diseases['hiv'].infected & age_mask)
    # Calculate prevalence as a percentage
    if population_in_group > 0:
        initial_prevalence[label] = (infected_in_group / population_in_group) * 100

# Print initial prevalence to compare with input values
print("Initial Prevalence by Age Group:")
for label, prevalence in initial_prevalence.items():
    print(f"Age Group {label}: {prevalence:.2f}%")

# Plot HIV prevalence by age group over time
for t in range(len(baseline_sim.yearvec)):
    ages = baseline_sim.people.age  # Get current ages of agents
    infected = baseline_sim.diseases['hiv'].infected  # Get infected status
    
    for (start, end), label in zip(left_right, age_group_labels):
        # Create a mask for agents in the current age group
        age_mask = (ages >= start) & (ages < end)
        # Count total population in this age group
        population_by_age_group[label][t] = np.sum(age_mask)
        # Count infected population in this age group
        infected_in_group = np.sum(infected & age_mask)
        # Calculate prevalence as a percentage
        if population_by_age_group[label][t] > 0:  # Avoid division by zero
            age_results[label][t] = (infected_in_group / population_by_age_group[label][t]) * 100

# Plot HIV prevalence by age group
fig_age, ax_age = pl.subplots(figsize=(12, 8))
for label in age_group_labels:
    ax_age.plot(baseline_sim.yearvec, age_results[label], label=label)

ax_age.set_title('HIV Prevalence by Age Group')
ax_age.set_xlabel('Year')
ax_age.set_ylabel('Prevalence (%)')
ax_age.legend(title='Age Groups')
ax_age.grid(True)

pl.tight_layout()
pl.show()
