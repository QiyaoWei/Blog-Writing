How DO people measure kl divergence?

## The idea of KL divergence

Some toy examples showing KL divergence between two vectors

If I can find some informational approach that would be even better

## KL divergence in language models

Nothing special. What you do is

(1) Calculate the logits. There could be a whole article about how to do this, but for now suffice to say that a forward pass of the model gives the logits of the next token.

What is the shape of the logits? \textit{logit} \in \mathbb{R}^{bs \times len \times words}

(2) Calculate the logprobs. As usual, the difference is that logits are the raw model predictions, and logprobs are what comes out of a torch.nn.functional.log_softmax() operation.

\textbf{Note:} What I slightly dislike is that there is one operation that's sweeped under the rug. Obviously, post-softmax logprobs and pre-softmax logits would have the same shape.
However, it clearly doesn't make sense to calculate the KL with respect to every single word in the dictionary, and therefore we have to index the correct position.
I think this is pretty intuitive, but it is important to outline everything that's happening here.
In sum, \textit{logprob} \in \mathbb{R}^{bs \times len}

(3) Calculate KL. Now that we have effectively two vectors, we can do our KL calculation with ease!
