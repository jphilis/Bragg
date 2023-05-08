from functools import cache
import sys

sys.set_int_max_str_digits(2000000)


@cache
def factorial(n):
    return n * factorial(n - 1) if n else 1


def factorial2(n):
    res = n
    while n > 1:
        n -= 1
        res *= n
    return res


N = 1000
for n in range(N + 1):
    fac = factorial(n)
print(len(str(fac)))

print(len(str(factorial2(N))))

# print(factorial(N))
# print(factorial2(N))
