# Poll Creation Syntax

`~poll make [rcv | fptp] [election_time_in_secs] [borda | irv | kemeny] [rcv_num_choices] [old_poll]`

## rcv | fptp

- `rcv` - ranked-choice voting
- `fptp` - first past the post

The two options have different interfaces for ballot filling. `rcv` ranks up to 4
choices using selection boxes. `fptp` selects a single favorite from a list of emoji.

## election_time_in_secs

Defaults to 86400 or one day.

## borda | irv | kemeny

This is the current list of methods for tabulating ranked votes. This only applies to
the `rcv` option. For `fptp` you can leave it blank or put garbage here. Discord doesn't
allow keyword arguments :(.

### Borda Count

The Borda Count is one of the simplest single-winner ranked tabulating methods.
Suppose each ballot ranks the voter's four top choices. 

Under this method, their first choice receives four points. Their second receives
three points, and so on.

Ties are possible in this method. In that case, a runoff should probably occur,
but right now the program will choose one arbitrarily.

### irv - Instant Runoff Voting

This is what ranked-choice voting usually refers to.

The winner is chosen over a series of elimination rounds. In each round, the candidate
that receives the lowest proportion of top choices is eliminated, and each ballot's top
choice is adjusted accordingly. This proceeds until one candidate receives a majority.

It is possible, even somewhat common, for this method to produce no winner because a
majority cannot be achieved. In that case, the program will switch to the Borda count.

### Kemeny

See section 4 of John Kemeny's paper, ["Mathematics Without Numbers"](https://www.jstor.org/stable/20026529).

Kemeny defined a notion of distance between orderings of candidates. The function $\mathrm{dist}(A,B)$ is defined as follows.

Consider all distinct pairs of candidates $(p, q)$. If orderings $A$ and $B$ agree on
the relative ranks of $p$ and $q$, add 0 to the total. If $A$ believe $p>q$ while $B$ believes $q>p$,
add 2 to the total. If one has a preference while the other does not, add 1 to the total. After all
pairs have been summed, the total is the distance between the orderings.

Now, consider an election $(C, B)$ where we have a set of candidates $C$ and a set of ballots $B$. The Kemeny Consensus is the ordering $X$
of $C$ which minimizes $\sum_{b\in B}\mathrm{dist}(b, X)$. The winner of the election is the first element of $X$.

Kemeny's method has some nice properties. For example, when one exists, it always yields the [Condorcet winner](https://en.wikipedia.org/wiki/Condorcet_winner_criterion),
the candidate who would beat all other candidates in a one-on-one race. Failing that, the winner will always come from the [Smith set](https://en.wikipedia.org/wiki/Smith_set),
an extension of the Condorcet winner to a subset of candidates.

## rcv_num_choices

Maxes at 4 because of Discord reasons.


## old_poll

Initialize an election from a stored poll. Currently this only work for `fptp`. You can just fill in garbage for the other arguments.