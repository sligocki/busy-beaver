# Runtime test for modular arithmetic on deep Exp_Ints.

import time

from Exp_Int import exp_int


def time_exp_int(max_depth):
  x = 105
  for d in range(max_depth):
    start = time.time()
    k, _ = divmod(x, 3)
    end = time.time()
    print(d, end-start)
    x = (61 * exp_int(4, k) - 13) / 3

time_exp_int(1000)

# With direct iteration cycle detection, runtimes are:
#   10 0.030209779739379883
#   11 0.10003399848937988
#   12 0.3085310459136963
#   13 1.2171227931976318
#   14 3.805593967437744
#   15 12.870368957519531
#   16 38.87016201019287
#   17 154.07067823410034
# So, exponential growth, becoming impractical somewhere in the 15-20 range.
# Memory use was also really high.

# Using Carmichael's lambda function, runtimes are:
#     100 0.0034961700439453125
#     200 0.017728805541992188
#     300 0.05291295051574707
#     400 0.12418699264526367
#     500 0.2540450096130371
#     600 0.4653170108795166
#     700 0.7906599044799805
#     800 1.2717199325561523
#     900 1.9026918411254883
#    1000 2.7404301166534424
# AKA, hella faster!  Maybe still exponential growth, but the base is waaaay smaller.
