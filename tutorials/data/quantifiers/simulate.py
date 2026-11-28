"""Simulate the salmon outputs of the quantifiers tutorial.

Writes, under the directory given (default: the directory holding this
script):

- salmon/S1/quant.sf ... salmon/S6/quant.sf: salmon's quant.sf for six
  samples, three ctrl and three treat, over 300 made-up transcripts
- salmon/P1/quant.sf: P1, a pilot library quantified with them, which is not
  part of the study
- samples.csv: the study's sample sheet, S1 to S6 and their condition

    python simulate.py [DIR]

The data are simulated, so they carry no licence question. The script uses
only the Python standard library and draws every random number from
random.Random(SEED).random(), whose sequence Python keeps the same from
version to version, and builds its own normal and Poisson draws on it, so
it writes the same bytes on every Python 3.11 or later. (The math module's
exp, log and cos come from the platform's C library; the tests check the
bytes on Linux.)
"""

import math
import random
import sys
from pathlib import Path

SEED = 20261120
N_TRANSCRIPTS = 300
SAMPLES = [
    ("S1", "ctrl"),
    ("S2", "ctrl"),
    ("S3", "ctrl"),
    ("S4", "treat"),
    ("S5", "treat"),
    ("S6", "treat"),
]
PILOT = ("P1", "ctrl")  # quantified, but not in the sample sheet
MEAN_FRAGMENT = 187.5  # one fragment length for every sample


def normal(rng, mean=0.0, sd=1.0):
    """A normal draw by the Box-Muller transform."""
    u1 = 1.0 - rng.random()  # in (0, 1], so the log is finite
    u2 = rng.random()
    return mean + sd * math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def poisson(rng, mu):
    """A Poisson draw: by inversion for a small mean, else rounded normal."""
    if mu < 30:
        k, p = 0, math.exp(-mu)
        cdf, u = p, rng.random()
        while u > cdf:
            k += 1
            p *= mu / k
            cdf += p
        return k
    return max(0, round(normal(rng, mu, math.sqrt(mu))))


def simulate(rng):
    """Return the transcripts, as (name, length, effective length), and each
    sample's NumReads, as a list per sample."""
    transcripts = []
    abundance = []  # relative molecules per transcript
    fold = []  # treat over ctrl
    for i in range(1, N_TRANSCRIPTS + 1):
        name = f"TX{i:05d}.{1 + int(rng.random() * 3)}"
        length = max(250, round(math.exp(normal(rng, 7.3, 0.6))))
        # Salmon's effective length: the length less the mean fragment
        # length; one fragment length for all samples, so it is the same
        # in every sample.
        effective = length - MEAN_FRAGMENT + 1
        transcripts.append((name, length, effective))
        # Mostly low abundances with a long tail, and some unexpressed.
        a = math.exp(normal(rng, 0.0, 2.0))
        if rng.random() < 0.08:
            a = 0.0
        abundance.append(a)
        r = rng.random()
        fold.append(4.0 if r < 0.05 else 0.25 if r < 0.10 else 1.0)

    reads = []
    for _, group in SAMPLES + [PILOT]:
        depth = 120_000 * math.exp(normal(rng, 0.0, 0.25))
        weights = [
            a * (f if group == "treat" else 1.0) * eff
            for a, f, (_, _, eff) in zip(abundance, fold, transcripts)
        ]
        total = sum(weights)
        sample = []
        for w in weights:
            # Biological variation between replicates, then sampling.
            mu = depth * w / total * math.exp(normal(rng, 0.0, 0.2))
            k = poisson(rng, mu)
            # Salmon's NumReads are expected counts: some reads are shared
            # with other transcripts, so some values are not whole.
            if k > 0 and rng.random() < 0.3:
                k = k - round(rng.random(), 3)
            sample.append(k)
        reads.append(sample)
    return transcripts, reads


def quant_sf(transcripts, numreads):
    """The text of a salmon quant.sf."""
    rpk = [n / eff for n, (_, _, eff) in zip(numreads, transcripts)]
    scale = 1e6 / sum(rpk)
    lines = ["Name\tLength\tEffectiveLength\tTPM\tNumReads"]
    for (name, length, eff), n, r in zip(transcripts, numreads, rpk):
        lines.append(f"{name}\t{length}\t{eff:.3f}\t{r * scale:.6f}\t{n:.3f}")
    return "\n".join(lines) + "\n"


def main(out):
    rng = random.Random(SEED)
    transcripts, reads = simulate(rng)
    for (sample, _), numreads in zip(SAMPLES + [PILOT], reads):
        path = out / "salmon" / sample / "quant.sf"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(quant_sf(transcripts, numreads), newline="\n")
    sheet = ["sample,condition"] + [f"{s},{g}" for s, g in SAMPLES]
    (out / "samples.csv").write_text("\n".join(sheet) + "\n", newline="\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
