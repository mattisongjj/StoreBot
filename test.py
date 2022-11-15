def sum_for_list(lst):
    highest = abs(sorted(lst, key=lambda n: abs(n), reverse=True)[0])
    primes = get_primes(highest)
    output = []
    for prime_number in primes:
        factor_of = []
        for number in lst:
            if number % prime_number == 0:
                factor_of.append(number)
        if len(factor_of) != 0:
            output.append([prime_number, sum(factor_of)])
    return output

def get_primes(number):
    primes = []
    if number >= 2:
        primes.append(2)
    for i in range(2, number + 1):
        for j in range(2, i):
            if i % j == 0:
                break
            if j == i - 1:
                primes.append(i)
    return primes