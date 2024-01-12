
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
