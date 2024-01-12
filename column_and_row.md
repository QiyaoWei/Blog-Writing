
***Julia***

Setup

```
A = rand(100, 100)
B = rand(100, 100)
C = rand(100, 100)
using BenchmarkTools
```

Now we can do

```
function inner_rows!(C, A, B)
  for i in 1:100, j in 1:100
    C[i,j] = A[i,j] + B[i,j]
  end
end
@btime inner_rows!(C, A, B)
```
12.941 μs (0 allocations: 0 bytes)

```
function inner_cols!(C, A, B)
  for j in 1:100, i in 1:100
    C[i,j] = A[i,j] + B[i,j]
  end
end
@btime inner_cols!(C, A, B)
```
12.407 μs (0 allocations: 0 bytes)


***Python(Numpy)***

Setup

```
import timeit
import time
import numpy as np
A = np.random.rand(100, 100)
B = np.random.rand(100, 100)
C = np.random.rand(100, 100)
```

Now we can do

```
def functionA(C, A, B):
  for i in range(100):
    for j in range(100):
      C[i,j] = A[i,j] + B[i,j]
start_time = timeit.default_timer()
functionA(C, A, B)
print(timeit.default_timer() - start_time)
```
0.007111948001693236

```
def functionB(C, A, B):
  for j in range(100):
    for i in range(100):
      C[i,j] = A[i,j] + B[i,j]
start_time = timeit.default_timer()
functionB(C, A, B)
print(timeit.default_timer() - start_time)
```
0.00885440799902426
