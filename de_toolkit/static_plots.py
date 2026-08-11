"""
Static SVG fallback for genomics-scale scatter plots (#5).

Vega-Lite with inline data is the primary chart path, but very large point
sets make the report page heavy and the hover sluggish. Above
``MAX_INTERACTIVE_POINTS`` the report swaps the interactive chart for a
matplotlib-rendered SVG with **rasterized** points: the axes, labels and
legend stay crisp vectors while the point cloud is a compact embedded image,
so a 50k-point volcano stays a few hundred kB instead of megabytes of DOM.

matplotlib renders with the Agg backend; no display is required.
"""

import io
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# above this many inline rows, a chart is rendered statically
MAX_INTERACTIVE_POINTS = 20000

# colors matched to the report's categorical palette
SIG_COLORS = {"up": "#e45756", "down": "#4c78a8", "ns": "#b0b0b0"}


def scatter_svg(rows, x, y, xlabel, ylabel, color_by="sig", title=None):
    """Render *rows* (list of dicts) as a scatter and return an SVG string.

    Points are rasterized inside the SVG; axes and text remain vectors.
    Raises ImportError when matplotlib is unavailable.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=110)
    try:
        order = ("ns", "down", "up")  # significant points drawn on top
        for cls in order:
            xs = [r[x] for r in rows if r.get(color_by, "ns") == cls and r.get(x) is not None]
            ys = [r[y] for r in rows if r.get(color_by, "ns") == cls and r.get(y) is not None]
            if not xs:
                continue
            ax.scatter(
                xs,
                ys,
                s=4,
                linewidths=0,
                alpha=0.6,
                color=SIG_COLORS.get(cls, "#b0b0b0"),
                label=cls,
                rasterized=True,
            )
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title, fontsize=11)
        ax.legend(frameon=False, fontsize=8, markerscale=2)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        fig.patch.set_alpha(0)  # transparent figure background for theming

        buf = io.StringIO()
        fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
        return buf.getvalue()
    finally:
        plt.close(fig)


def svg_view(rows, x, y, xlabel, ylabel, note=None, title=None):
    """Build an ``{"type": "svg"}`` report view, or a raw view if matplotlib
    is missing (the report never breaks over a chart)."""
    try:
        svg = scatter_svg(rows, x, y, xlabel, ylabel, title=title)
    except ImportError:
        logger.warning("matplotlib unavailable; large chart falls back to raw view")
        return {
            "type": "raw",
            "error": "matplotlib is required to render charts this large statically",
        }
    view = {"type": "svg", "svg": svg}
    if note:
        view["note"] = note
    return view
