##Reference: Natasha Jaques https://www.youtube.com/watch?v=56PlUikhB3o##

1. KL-control from pre-trained data prior $p(a|s)$
   
   $$L(q) = E_{q(\tau)} \frac{[r(\tau)]}{c} - D_{KL} [q(\tau) || p(\tau)]
   $$

   In terms of Q-learning, this is simply

   $$Q^{\pi}(s_{t}, a_{t}) = E_{\pi} [\sum_{t'=t}^{T} \frac{r(s_{t}, a_{t})}{c} - log \pi(a_{t'}|s_{t'}) + log p(a_{t'}|s_{t'})]
   $$

2. Reward function

   The probability of preferring segment $\sigma^{1}$ is described as

   $$\hat P[\sigma^{1} > \sigma^{2}] = \frac{exp \sum \hat r(o^{1}_{t}, a^{1}_{t})}{exp \sum \hat r(o^{1}_{t}, a^{1}_{t}) + exp \sum \hat r(o^{2}_{t}, a^{2}_{t})}
   $$

   And the loss function for learning the reward function looks like

   $$loss(\hat r) = - \sum_{\sigma^{1}, \sigma^{2}, \mu \in \mathcal{D}} \mu(1) log \hat P[\sigma^{1} > \sigma^{2}] + \mu(2) log \hat P[\sigma^{2} > \sigma^{1}]
   $$

   where $\mu = [1,0] or [0,1] or [0.5,0.5]$
