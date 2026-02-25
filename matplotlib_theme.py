#!/usr/bin/env python
# coding: utf-8

# matplotlib_theme.py

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


# --------------------------------------------------------
# Alap téma – minden ábrára érvényes
# --------------------------------------------------------
def apply_default_theme():
    plt.style.use("default")
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",

        # MÓDOSÍTÁS: gridline kikapcsolva alapból
        "axes.grid": False,

        "grid.color": "#DDDDDD",
        "grid.linestyle": "-",
        "grid.alpha": 0.6,
        "axes.edgecolor": "#333333",
        "axes.labelcolor": "#333333",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "lines.linewidth": 2,
        "lines.markersize": 5,
    })


# --------------------------------------------------------
# Y tengely mindig 0-ról indul
# --------------------------------------------------------
def force_zero_y_axis(ax):
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(bottom=0)


# --------------------------------------------------------
# DÁTUMTENGELY FORMÁZÓ
# --------------------------------------------------------
def format_date_axis(ax):

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y-%m")
    )

    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment("right")

    force_zero_y_axis(ax)

    plt.tight_layout()


# --------------------------------------------------------
# Általános DÁTUMTENGELY FORMÁZÓ
# --------------------------------------------------------

def format_date(ax, kind="line"):

    import matplotlib.dates as mdates

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y-%m")
    )

    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment("right")

    if kind == "bar":
        width = 25.0
        for bar in ax.patches:
            bar.set_width(width)

    force_zero_y_axis(ax)

    plt.tight_layout()


# --------------------------------------------------------
# VONALDIAGRAM FORMÁZÓ
# --------------------------------------------------------
def format_line(ax):

    ax.grid(True, linestyle="-", alpha=0.4)

    plt.setp(
        ax.get_xticklabels(),
        rotation=45,
        ha="right"
    )

    force_zero_y_axis(ax)


# --------------------------------------------------------
# OSZLOPDIAGRAM FORMÁZÓ
# --------------------------------------------------------
def format_bar(ax):

    ax.grid(True, axis="y", linestyle="-", alpha=0.4)

    plt.setp(
        ax.get_xticklabels(),
        rotation=45,
        ha="right"
    )

    force_zero_y_axis(ax)


# --------------------------------------------------------
# KÖRDIAGRAM FORMÁZÓ
# --------------------------------------------------------
def format_pie(ax):
    ax.set_aspect("equal")