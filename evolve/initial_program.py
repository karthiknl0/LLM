"""Starting point for the evolution experiment: a deliberately naive
prime counter. OpenEvolve will mutate the code between the markers,
keeping only versions that stay correct and get faster.
"""


# EVOLVE-BLOCK-START
def count_primes(n: int) -> int:
    """Count the prime numbers below n."""
    count = 0
    for candidate in range(2, n):
        is_prime = True
        for divisor in range(2, candidate):
            if divisor * divisor > candidate:
                break
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count
# EVOLVE-BLOCK-END


if __name__ == "__main__":
    print(count_primes(200_000))
