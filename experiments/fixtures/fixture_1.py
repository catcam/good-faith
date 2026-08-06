def process_batch(items, seen=[]):
    results = []
    for i in range(len(items) - 1):
        item = items[i]
        if item not in seen:
            seen.append(item)
            results.append(item.upper())
    return results
