"""
Use this program as a template for experimenting with the Metropolis algorithm
applied to 2 parameters called theta1,theta2 defined on the domain [0,1]x[0,1].
"""
from __future__ import division
import numpy as np
from scipy.stats import beta
import matplotlib.pyplot as plt


# Define the likelihood function.
# The input argument is a vector: theta = [theta1 , theta2]

def likelihood(theta):
    # Data are constants, specified here:
    z1, N1, z2, N2 = 5, 7, 2, 7
    likelihood = (theta[0]**z1 * (1-theta[0])**(N1-z1)
                 * theta[1]**z2 * (1-theta[1])**(N2-z2))
    return likelihood


# Define the prior density function.
# The input argument is a vector: theta = [theta1 , theta2]
def prior(theta):
    # Here's a beta-beta prior:
    a1, b1, a2, b2 = 3, 3, 3, 3
    prior = beta.pdf(theta[0], a1, b1) * beta.pdf(theta[1], a2, b2) 
    return prior


# Define the relative probability of the target distribution, as a function 
# of theta.  The input argument is a vector: theta = [theta1 , theta2].
# For our purposes, the value returned is the UNnormalized posterior prob.
def target_rel_prob(theta):
    if ((theta >= 0.0).all() & (theta <= 1.0).all()):
        target_rel_probVal =  likelihood(theta) * prior(theta)
    else:
        # This part is important so that the Metropolis algorithm
        # never accepts a jump to an invalid parameter value.
        target_rel_probVal = 0.0
    return target_rel_probVal
#    if ( all( theta >= 0.0 ) & all( theta <= 1.0 ) ) {
#        target_rel_probVal =  likelihood( theta ) * prior( theta )


# Specify the length of the trajectory, i.e., the number of jumps to try:
traj_length = 5000 # arbitrary large number
# Initialize the vector that will store the results.
trajectory = np.zeros((traj_length, 2))
# Specify where to start the trajectory
trajectory[0, ] = [0.50, 0.50] # arbitrary start values of the two param's
# Specify the burn-in period.
burn_in = np.ceil(.1 * traj_length).astype(int) # arbitrary number
# Initialize accepted, rejected counters, just to monitor performance.
n_accepted = 0
n_rejected = 0
# Specify the seed, so the trajectory can be reproduced.
np.random.seed(47405)
# Specify the covariance matrix for multivariate normal proposal distribution.
n_dim, sd1, sd2 = 2, 0.2, 0.2
covar_mat = [[sd1**2, 0], [0, sd2**2]]

# Now generate the random walk. step is the step in the walk.
for step in range(traj_length-1):
    current_position = trajectory[step, ]
    # Use the proposal distribution to generate a proposed jump.
    # The shape and variance of the proposal distribution can be changed
    # to whatever you think is appropriate for the target distribution.
    proposed_jump = np.random.multivariate_normal(mean=np.zeros((n_dim)),
                                                 cov=covar_mat)
    # Compute the probability of accepting the proposed jump.
    prob_accept = np.minimum(1, target_rel_prob(current_position + proposed_jump)
                            / target_rel_prob(current_position))
    # Generate a random uniform value from the interval [0,1] to
    # decide whether or not to accept the proposed jump.
    if np.random.rand() < prob_accept:
        # accept the proposed jump
        trajectory[step+1, ] = current_position + proposed_jump
        # increment the accepted counter, just to monitor performance
        if step > burn_in:
            n_accepted += 1
    else:
        # reject the proposed jump, stay at current position
        trajectory[step+1, ] = current_position
        # increment the rejected counter, just to monitor performance
        if step > burn_in:
            n_rejected += 1

# End of Metropolis algorithm.

#-----------------------------------------------------------------------
# Begin making inferences by using the sample generated by the
# Metropolis algorithm.

# Extract just the post-burnIn portion of the trajectory.
accepted_traj = trajectory[burn_in:]

# Compute the means of the accepted points.
mean_traj =  np.mean(accepted_traj, axis=0)
# Compute the standard deviations of the accepted points.
stdTraj =  np.std(accepted_traj, axis=0)

# Plot the trajectory of the last 500 sampled values.
plt.plot(accepted_traj[:,0], accepted_traj[:,1], marker='o', alpha=0.3)
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.xlabel(r'$\theta1$')
plt.ylabel(r'$\theta2$')

# Display means in plot.
plt.plot(0, label='M = %.3f, %.3f' % (mean_traj[0], mean_traj[1]), alpha=0.0)
# Display rejected/accepted ratio in the plot.
plt.plot(0, label=r'$N_{pro}=%s$ $\frac{N_{acc}}{N_{pro}} = %.3f$' % (len(accepted_traj), (n_accepted/len(accepted_traj))), alpha=0)

# Evidence for model, p(D).
# Compute a,b parameters for beta distribution that has the same mean
# and stdev as the sample from the posterior. This is a useful choice
# when the likelihood function is binomial.
a =   mean_traj * ((mean_traj*(1-mean_traj)/stdTraj**2) - np.ones(n_dim))
b = (1-mean_traj) * ( (mean_traj*(1-mean_traj)/stdTraj**2) - np.ones(n_dim))
# For every theta value in the posterior sample, compute 
# beta.pdf(theta, a, b) / likelihood(theta) * prior(theta)
# This computation assumes that likelihood and prior are properly normalized,
# i.e., not just relative probabilities.

wtd_evid = np.zeros(np.shape(accepted_traj)[0])
for idx in range(np.shape(accepted_traj)[0]):
    wtd_evid[idx] = (beta.pdf(accepted_traj[idx,0],a[0],b[0] )
        * beta.pdf(accepted_traj[idx,1],a[1],b[1]) /
        (likelihood(accepted_traj[idx,]) * prior(accepted_traj[idx,])))

p_data = 1 / np.mean(wtd_evid)
# Display p(D) in the graph
plt.plot(0, label='p(D) = %.3e' % p_data, alpha=0)
plt.legend(loc='upper left')
plt.savefig('Figure_8.3.png')

# Estimate highest density region by evaluating posterior at each point.
accepted_traj = trajectory[burn_in:]
npts = np.shape(accepted_traj)[0] 
post_prob = np.zeros((npts))
for ptIdx in range(npts):
    post_prob[ptIdx] = target_rel_prob(accepted_traj[ptIdx,])

# Determine the level at which credmass points are above:
credmass = 0.95
waterline = np.percentile(post_prob, (credmass))

HDI_points = accepted_traj[post_prob > waterline, ]

plt.figure()
plt.plot(HDI_points[:,0], HDI_points[:,1], 'ro')
plt.xlim(0,1)
plt.ylim(0,1)
plt.xlabel(r'$\theta1$')
plt.ylabel(r'$\theta2$')

# Display means in plot.
plt.plot(0, label='M = %.3f, %.3f' % (mean_traj[0], mean_traj[1]), alpha=0.0)
# Display rejected/accepted ratio in the plot.
plt.plot(0, label=r'$N_{pro}=%s$ $\frac{N_{acc}}{N_{pro}} = %.3f$' % (len(accepted_traj), (n_accepted/len(accepted_traj))), alpha=0)
# Display p(D) in the graph
plt.plot(0, label='p(D) = %.3e' % p_data, alpha=0)
plt.legend(loc='upper left')

plt.savefig('Figure_8.3_HDI.png')

plt.show()

