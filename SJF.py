n = 3
bt = [6, 8, 7]

bt.sort()
wt = [0, bt[0], bt[0]+bt[1]]
tat = [bt[i]+wt[i] for i in range(n)]

print(f"{'Process':<8}{'BT':<6}{'WT':<6}{'TAT':<6}")

for i in range(n):
    print(f"{'P'+str(i+1):<8}{bt[i]:<6}{wt[i]:<6}{tat[i]:<6}")
print(f"\nAverage Waiting Time: {sum(wt)/n:.2f}")
print(f"Average Turnaround Time: {sum(tat)/n:.2f}")