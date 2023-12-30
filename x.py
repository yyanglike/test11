import time

start_time = time.time()

for i in range(2400000):
    if i % 2 == 0:
        x = i * 3.124
        x /= 4.52
        x *= 0.21
        pass

end_time = time.time()

print(f"Total execution time: {end_time - start_time} seconds")
