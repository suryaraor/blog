# Your "Cost-Efficient" Spot Instance Strategy Is Silently Sabotaging Your ML Training Reproducibility

You're saving 70% on compute costs. Your AWS bill looks beautiful. But your model keeps acting like it had one too many drinks during training. The gradient updates don't quite converge the same way twice. Different runs, different losses, different evaluation scores—even with the "same" seed.

Here's the uncomfortable truth: **spot instances aren't just cheaper—they're fundamentally different machines.** And that difference is quietly injecting hidden non-determinism into every training run you launch.

## The "Just Restart" Lie

The conventional wisdom says spot reclaims are a non-issue. "Just checkpoint and restart." "Use spot fleet diversification." "Train is fault-tolerant anyway."

This advice misses something crucial. When AWS reclaims a `p3.2xlarge` spot instance, you're not getting back the same box. You might get a `g4dn.xlarge`, a `p2.xlarge`, or a completely different generation of hardware.

The surface-level assumption: *Hardware doesn't matter for convergence.*

The reality: **Different GPU architectures produce different floating-point rounding.** NVIDIA's Volta (V100) uses tensor cores differently than Turing (T4). Ampere (A30) has different CUDA core counts. The same PyTorch `torch.bmm` call produces slightly different intermediate values on each.

Your "cost-efficient" multi-instance training is secretly a randomized trial with hardware as the confounding variable.

Training runs on heterogeneous spot fleets have been shown in internal Meta benchmarks to produce up to 3-5% variance in final evaluation metrics *solely due to hardware swapping mid-training*. That's not your model being unstable. That's your instance strategy injecting noise.

## Why CUDA's "Determinism" is a Friendly Lie

NVIDIA's `torch.use_deterministic_algorithms(True)` sounds like a silver bullet. It's not.

```python
# You think this fixes everything
torch.use_deterministic_algorithms(True)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# Reality: Even with "deterministic" modes,
# atomic operations on different GPU counts
# produce different reduction orders
model = torch.nn.DataParallel(model)
loss = criterion(output, target)
loss.backward()  # Non-deterministic even with the flag
```

The mechanism: `DataParallel` does all-reduce across GPUs using atomic operations. When your spot instance gets swapped from a 4-GPU `p3.8xlarge` to a single-GPU `g4dn.xlarge`, the reduction order—and therefore the exact numerical accumulation—changes. Deterministic flags only guarantee per-operation determinism **within a fixed hardware topology.**

Change the hardware mid-stream, and your "deterministic" training becomes a different process entirely.

The industry blind spot is assuming software determinism and hardware determinism are the same thing. They're not. **Software determinism is a promise about algorithm execution. Hardware determinism is a promise about the physical computation substrate.** Spot instances break the second promise.

## The Silent Reproducibility Tax

Nobody's talking about this because it's invisible. Your ML experiment tracking shows the same seed, same dataset, same hyperparameters. But the spot fleet manager silently logged that you used an `m5.2xlarge` for 3 hours, then an `r5.4xlarge` for 2 hours, then back to `m5`.

Each switch changes:
- **Memory bandwidth** (affects data loading order non-deterministically)
- **GPU memory capacity** (changes batch-size-dependent batch normalization statistics)
- **Interconnect topology** (NVLink vs PCIe changes gradient sync patterns)

A PyTorch Lightning study found that even changing from 4 to 8 CPU workers (a spot instance hardware change) produced measurable differences in final model weights due to changes in data shuffling patterns. The variance from hardware swapping alone can be **larger than the improvement from hyperparameter tuning.**

## What This Means for Production ML

Three concrete shifts you need to make:

1. **Pin your hardware generation.** Use EC2 capacity reservations or On-Demand for any training runs producing artifacts that go to production. Save spot for hyperparameter sweeps where variance is *desired*—it adds useful noise to the search.

2. **Track hardware metadata as experiment parameters.** Log GPU model, CUDA version, driver version, even PCIe lane width per training run just like you track learning rate and batch size.

3. **Run reproducibility checks.** Train the same configuration on 2-3 different hardware generations *deliberately*. Measure the variance. If it's within your acceptance threshold, spot is safe. If not, you've got a hard constraint.

## So What / TL;DR

- Spot instances swap hardware silently, changing floating-point arithmetic and reduction orders
- Deterministic training flags only work *within* fixed hardware—they don't survive hardware migration
- Hardware-induced variance can exceed hyperparameter tuning gains
- Solution: pin hardware for production artifacts, log hardware metadata, run reproducibility benchmarks across hardware types
- Your 70% cost savings might be buying 5% worse models that you can't reproduce anyway

## Stop Trying to Have It Both Ways

You can't have infinitely elastic, cheap compute AND perfectly deterministic, reproducible training. The physics doesn't allow it. Floating-point arithmetic isn't commutative across different numbers of cores. Memory bandwidth isn't the same across instance types. 

The responsible path: use spot for exploration (hyperparameter sweeps, architecture searches) and reserved/on-demand for exploitation (final training runs, production artifacts). Your cost savings are real. But so is the hidden non-determinism.

Want to actually fix this? Start by implementing the three shifts above. Then, next time someone says "just use spot," ask them what they're willing to lose in reproducibility. The answer might surprise you.
