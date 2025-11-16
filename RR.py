n = int(input("Processes: "))
tq = int(input("Time Quantum: "))
a, b = [], []
for i in range(n):
    a.append(int(input(f"AT P{i+1}: ")))
    b.append(int(input(f"BT P{i+1}: ")))

r, w, t, m, q, g, time = b[:], [0]*n, [0]*n, [0]*n, [0], [], 0
m[0] = 1

while q:
    i = q.pop(0)
    if r[i] == b[i]: time = max(time, a[i])
    d = min(tq, r[i])
    g.append((f"P{i+1}", time, time+d))
    time += d
    r[i] -= d
    if r[i] == 0:
        t[i] = time - a[i]
        w[i] = t[i] - b[i]
    for j in range(n):
        if r[j] > 0 and a[j] <= time and not m[j]: q.append(j); m[j] = 1
    if r[i] > 0: q.append(i)
    if not q:
        for j in range(n):
            if r[j] > 0: q.append(j); m[j] = 1; break

print(f"\nAvg WT = {sum(w)/n:.2f}, Avg TAT = {sum(t)/n:.2f}")
print("\nGantt Chart:")
for p, s, e in g: print(f"| {p} ", end="")
print("|")
for _, s, _ in g: print(f"{s:<5}", end="")
print(f"{g[-1][2]}")