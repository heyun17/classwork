from measure import measure, append_row

def heavy_work():
    return [0] * 10_000_000

for i in range(5):
    row, _ = measure(heavy_work, target="list_10m", action="alloc")
    append_row(row)
    print(i, row["elapsed_s"])