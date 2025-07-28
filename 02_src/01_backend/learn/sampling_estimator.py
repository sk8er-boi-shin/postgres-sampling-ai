def estimate_sample_size(metrics):
    return max(100, int(metrics["reltuples"] * 0.01))
