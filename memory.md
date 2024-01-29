
# Column major and row major

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

# Heap allocations

***Julia***

```
function inner_alloc!(C,A,B)
  for j in 1:100, i in 1:100
    val = [A[i,j] + B[i,j]]
    C[i,j] = val[1]
  end
end
@btime inner_alloc!(C,A,B)
```
208.801 μs (10000 allocations: 937.50 KiB)

```
function inner_noalloc!(C,A,B)
  for j in 1:100, i in 1:100
    val = A[i,j] + B[i,j]
    C[i,j] = val[1]
  end
end
@btime inner_noalloc!(C,A,B)
```
6.520 μs (0 allocations: 0 bytes)

```
function inner_alloc(A,B)
  C = similar(A)
  for j in 1:100, i in 1:100
    val = A[i,j] + B[i,j]
    C[i,j] = val[1]
  end
end
@btime inner_alloc(A,B)
```
10.700 μs (2 allocations: 78.20 KiB)

```
function unfused(A,B,C)
  tmp = A .+ B
  tmp .+ C
end
@btime unfused(A,B,C);
```
12.999 μs (4 allocations: 156.41 KiB)

```
fused(A,B,C) = A .+ B .+ C
@btime fused(A,B,C);
```
5.875 μs (2 allocations: 78.20 KiB)

```
D = similar(A)
fused!(D,A,B,C) = (D .= A .+ B .+ C)
@btime fused!(D,A,B,C);
```
3.775 μs (0 allocations: 0 bytes)
