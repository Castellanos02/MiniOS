#!/usr/bin/env python3
"""
visualize_spikes.py
===================
Publication-quality spike raster & firing-rate visualisations for MiniOS SNN.
Aesthetic target: Nature Communications / Fig. 4 style (Pedersen et al. 2024).

Usage
-----
# Within train_usecase_snn.py (automatic):
    from visualize_spikes import SpikeVisualizer
    viz = SpikeVisualizer()
    viz.plot_lif_panel(spk_out, mem_rec, input_spk, epoch=5)
    viz.plot_similarity_heatmap(sim_matrix, platform_names)

# Standalone demo:
    python visualize_spikes.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# Journal-style rcParams  (matches Nature Comms sans-serif look)
# ─────────────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "font.size":          8,
    "axes.linewidth":     0.6,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.labelsize":     8,
    "axes.titlesize":     9,
    "xtick.major.width":  0.6,
    "ytick.major.width":  0.6,
    "xtick.major.size":   3,
    "ytick.major.size":   3,
    "xtick.labelsize":    7,
    "ytick.labelsize":    7,
    "legend.fontsize":    7,
    "legend.frameon":     False,
    "figure.dpi":         150,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
    "savefig.facecolor":  "white",
    "axes.facecolor":     "white",
    "figure.facecolor":   "white",
    "lines.linewidth":    0.9,
})

# ─────────────────────────────────────────────────────────────────────────────
# Colour palette — one distinct colour per activity/neuron (20 outputs)
# ─────────────────────────────────────────────────────────────────────────────
ACTIVITY_LABELS = [
    "quick_rest", "stretch_break", "quick_task", "workout", "lunch_break",
    "creative_work", "light_activity", "deep_work", "productive_project",
    "relax", "hobby_time", "flexible_activity",
    "prepare_meeting", "review_notes", "stay_ready",
    "check_in", "music", "podcast",
    "route", "social",
]

_TRACE_COLORS = [
    "#E07B39", "#4A90D9", "#5BAD72", "#C94F4F", "#9B6BB5",
    "#D4A843", "#4BB8C4", "#E87BAC", "#7A9E3B", "#6E7BCC",
    "#C97A3A", "#3D9E8C", "#B85C8A", "#8AAE4D", "#5577BB",
    "#D46B6B", "#52A89E", "#C4884F", "#7BA85B", "#A06EC4",
]

# Blue-white colormap for cosine-similarity / rate heatmaps
_SIM_CMAP = LinearSegmentedColormap.from_list(
    "sim_blue", ["#FFFFFF", "#C8DCEF", "#6BAED6", "#2171B5", "#08306B"], N=256
)


def _draw_spike_ticks(ax, spike_array_1d, y_center=0.5, height=0.85,
                      color="black", lw=0.8):
    t_spikes = np.where(np.asarray(spike_array_1d) > 0.5)[0]
    for t in t_spikes:
        ax.plot([t, t], [y_center - height/2, y_center + height/2],
                color=color, lw=lw, solid_capstyle="butt")


class SpikeVisualizer:
    """
    Publication-quality visualiser matching the Nature Communications
    Fig. 4 style (Pedersen et al., 2024).

    Parameters
    ----------
    output_dir : str
        Directory where PNG files are written.
    """

    def __init__(self, output_dir: str = "spike_plots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # =========================================================================
    # 1.  LIF PANEL  –  matches paper Fig. 4 (a)
    # =========================================================================
    def plot_lif_panel(self,
                       spk_out,
                       mem_rec,
                       spk_in=None,
                       neuron_labels=None,
                       epoch=None,
                       title="Single leaky integrate-and-fire neuron",
                       sample_idx=0,
                       max_neurons=10,
                       save=True):
        labels  = neuron_labels or ACTIVITY_LABELS
        spk_out = np.asarray(spk_out)
        mem_rec = np.asarray(mem_rec)

        if spk_out.ndim == 3:
            spk_out = spk_out[:, sample_idx, :]
        if mem_rec.ndim == 3:
            mem_rec = mem_rec[:, sample_idx, :]

        T, n_neurons = spk_out.shape
        n_show = min(max_neurons, n_neurons)

        mem_norm = np.zeros_like(mem_rec[:, :n_show])
        for i in range(n_show):
            col = mem_rec[:, i]
            lo, hi = col.min(), col.max()
            mem_norm[:, i] = (col - lo) / (hi - lo + 1e-9)

        if spk_in is None:
            spk_in = np.zeros(T)
        spk_in = np.asarray(spk_in)
        if spk_in.ndim == 2:
            spk_in = spk_in[:, sample_idx]

        fig = plt.figure(figsize=(9, 4.8))
        gs  = gridspec.GridSpec(3, 1, height_ratios=[0.8, 3.5, 0.8],
                                hspace=0.08, left=0.10, right=0.76,
                                top=0.88, bottom=0.12)

        ax_in   = fig.add_subplot(gs[0])
        ax_volt = fig.add_subplot(gs[1], sharex=ax_in)
        ax_out  = fig.add_subplot(gs[2], sharex=ax_in)

        # Input spikes
        ax_in.set_facecolor("white")
        _draw_spike_ticks(ax_in, spk_in, color="black", lw=0.9)
        ax_in.set_ylim(0, 1)
        ax_in.set_yticks([])
        ax_in.set_ylabel("Input", fontsize=7, labelpad=4)
        ax_in.tick_params(labelbottom=False)
        ax_in.spines["bottom"].set_visible(False)
        ax_in.spines["left"].set_linewidth(0.4)
        ax_in.set_title(title + (f"  ·  Epoch {epoch}" if epoch else ""),
                        fontsize=9, pad=5, loc="center")

        # Voltage traces
        ax_volt.set_facecolor("#F5F8FC")
        offset_step = 1.05
        for i in range(n_show - 1, -1, -1):
            offset = i * offset_step
            color  = _TRACE_COLORS[i % len(_TRACE_COLORS)]
            ax_volt.plot(mem_norm[:, i] + offset, color=color,
                         lw=0.85, alpha=0.92, zorder=n_show - i,
                         label=labels[i] if i < len(labels) else f"N{i}")
        ax_volt.set_ylim(-0.3, n_show * offset_step + 0.2)
        ax_volt.set_yticks([])
        ax_volt.set_ylabel("Voltage", fontsize=7, labelpad=4)
        ax_volt.tick_params(labelbottom=False)
        ax_volt.spines["bottom"].set_visible(False)
        ax_volt.spines["left"].set_linewidth(0.4)

        # Output spikes
        ax_out.set_facecolor("white")
        for i in range(n_show):
            t_sp = np.where(spk_out[:, i] > 0.5)[0]
            col  = _TRACE_COLORS[i % len(_TRACE_COLORS)]
            if t_sp.size:
                ax_out.plot(t_sp, np.ones_like(t_sp) * 0.5,
                            marker="+", ms=5, mew=0.9,
                            color=col, ls="none", zorder=2)
        ax_out.set_ylim(0, 1)
        ax_out.set_yticks([])
        ax_out.set_ylabel("Spikes", fontsize=7, labelpad=4)
        ax_out.set_xlabel("Timestep", fontsize=8)
        ax_out.spines["left"].set_linewidth(0.4)
        ax_out.xaxis.set_major_locator(ticker.MultipleLocator(max(1, T // 5)))
        ax_out.set_xlim(-0.5, T - 0.5)

        # Right-side legend (paper style)
        handles, lbs_leg = ax_volt.get_legend_handles_labels()
        fig.legend(handles[::-1], lbs_leg[::-1],
                   loc="center left",
                   bbox_to_anchor=(0.77, 0.50),
                   fontsize=6.5,
                   handlelength=1.4,
                   handletextpad=0.4,
                   borderpad=0.5,
                   title="Activity",
                   title_fontsize=7,
                   frameon=False)

        # Bracket annotation
        fig.text(0.975, 0.72, "Output\nLayer", fontsize=6.5,
                 ha="center", va="center", color="#555555", rotation=90)
        fig.add_artist(plt.Line2D([0.965, 0.965], [0.55, 0.89],
                                  transform=fig.transFigure,
                                  color="#888888", lw=0.8))

        path = ""
        if save:
            tag   = f"_epoch{epoch}" if epoch else ""
            fname = f"lif_panel{tag}.png"
            path  = os.path.join(self.output_dir, fname)
            fig.savefig(path)
            print(f"  ✓ LIF panel saved → {path}")
        plt.close(fig)
        return path

    # =========================================================================
    # 2.  SPIKE RASTER  –  paper Fig. 3e style
    # =========================================================================
    def plot_raster(self, spk_data, layer_name="Output Layer",
                    sample_idx=0, epoch=None, neuron_labels=None, save=True):
        arr = np.asarray(spk_data)
        if arr.ndim == 3:
            arr = arr[:, sample_idx, :]
        T, n_neurons = arr.shape
        labels = neuron_labels or ACTIVITY_LABELS

        fig_h = max(2.4, n_neurons * 0.22)
        fig, ax = plt.subplots(figsize=(8, fig_h))

        for ni in range(n_neurons):
            t_sp = np.where(arr[:, ni] > 0.5)[0]
            if t_sp.size:
                ax.vlines(t_sp, ni + 0.08, ni + 0.92,
                          color=_TRACE_COLORS[ni % len(_TRACE_COLORS)],
                          lw=1.1, alpha=0.85)

        if labels and len(labels) >= n_neurons:
            ax.set_yticks(np.arange(n_neurons) + 0.5)
            ax.set_yticklabels(labels[:n_neurons], fontsize=6.5)
        else:
            step = max(1, n_neurons // 8)
            ax.set_yticks(np.arange(0, n_neurons, step) + 0.5)
            ax.set_yticklabels([f"N{i}" for i in range(0, n_neurons, step)], fontsize=7)

        ax.set_ylim(0, n_neurons)
        ax.set_xlim(-0.5, T - 0.5)
        ax.invert_yaxis()
        ax.set_xlabel("Timestep", fontsize=8)
        ax.set_ylabel("Neuron", fontsize=8)
        epoch_tag = f"  ·  Epoch {epoch}" if epoch else ""
        ax.set_title(f"Spike Raster  ·  {layer_name}{epoch_tag}", fontsize=9)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(max(1, T // 5)))

        sparsity = 1.0 - arr.mean()
        ax.text(0.99, 0.01,
                f"sparsity {sparsity:.1%}  |  {int(arr.sum())} spikes",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=6.5, color="#555555")

        fig.tight_layout(pad=0.8)
        path = ""
        if save:
            tag   = f"_epoch{epoch}" if epoch else ""
            fname = f"raster_{layer_name.replace(' ', '_').lower()}{tag}.png"
            path  = os.path.join(self.output_dir, fname)
            fig.savefig(path)
            print(f"  ✓ Raster plot saved → {path}")
        plt.close(fig)
        return path

    # =========================================================================
    # 3.  COSINE-SIMILARITY HEATMAP  –  paper Fig. 4 (b/c/d)
    # =========================================================================
    def plot_similarity_heatmap(self, sim_matrix, platform_names,
                                title="Activity Similarity",
                                save=True, fname_tag=""):
        sim = np.asarray(sim_matrix)
        N   = sim.shape[0]

        fig_sz = max(3.0, N * 0.55)
        fig, ax = plt.subplots(figsize=(fig_sz, fig_sz * 0.9))

        im = ax.imshow(sim, cmap=_SIM_CMAP, vmin=0.0, vmax=1.0,
                       aspect="equal", interpolation="nearest")

        for r in range(N):
            for c in range(N):
                val  = sim[r, c]
                tcol = "white" if val > 0.65 else "black"
                ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                        fontsize=6.5, color=tcol)

        ax.set_xticks(range(N))
        ax.set_yticks(range(N))
        ax.set_xticklabels(platform_names, rotation=45, ha="right", fontsize=7)
        ax.set_yticklabels(platform_names, fontsize=7)
        ax.set_title(title, fontsize=9, pad=6)

        cbar = fig.colorbar(im, ax=ax, fraction=0.036, pad=0.04)
        cbar.set_label("Activity similarity", fontsize=7)
        cbar.ax.tick_params(labelsize=6.5)
        cbar.set_ticks([0.0, 0.5, 1.0])

        fig.tight_layout(pad=0.8)
        path = ""
        if save:
            fname = f"similarity_heatmap{fname_tag}.png"
            path  = os.path.join(self.output_dir, fname)
            fig.savefig(path)
            print(f"  ✓ Similarity heatmap saved → {path}")
        plt.close(fig)
        return path

    # =========================================================================
    # 4.  FIRING RATE BAR
    # =========================================================================
    def plot_firing_rate(self, spk_data, layer_name="Output Layer",
                         sample_idx=0, epoch=None, neuron_labels=None, save=True):
        arr = np.asarray(spk_data)
        if arr.ndim == 3:
            arr = arr[:, sample_idx, :]
        T, n_neurons = arr.shape
        rates  = arr.sum(0) / T
        winner = int(rates.argmax())
        labels = neuron_labels or ACTIVITY_LABELS

        fig_h = max(2.4, n_neurons * 0.24)
        fig, ax = plt.subplots(figsize=(6, fig_h))

        bar_colors = [_TRACE_COLORS[i % len(_TRACE_COLORS)] for i in range(n_neurons)]
        brs = ax.barh(range(n_neurons), rates, color=bar_colors,
                      height=0.72, alpha=0.85, edgecolor="none")
        brs[winner].set_edgecolor("#333333")
        brs[winner].set_linewidth(1.0)

        for i, rate in enumerate(rates):
            if rate > 0.005:
                ax.text(rate + rates.max() * 0.01, i, f"{rate:.3f}",
                        va="center", fontsize=6, color="#333333")

        wlabel = labels[winner] if winner < len(labels) else f"N{winner}"
        ax.text(0.98, 0.01, f"▶  {wlabel}",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8, color="#333333", fontweight="bold")

        if labels and len(labels) >= n_neurons:
            ax.set_yticks(range(n_neurons))
            ax.set_yticklabels(labels[:n_neurons], fontsize=6.5)
        else:
            step = max(1, n_neurons // 8)
            ax.set_yticks(range(0, n_neurons, step))
            ax.set_yticklabels([f"N{i}" for i in range(0, n_neurons, step)], fontsize=7)

        ax.invert_yaxis()
        ax.set_xlim(0, max(rates.max() * 1.20, 0.05))
        ax.set_xlabel("Mean spikes / timestep", fontsize=8)
        epoch_tag = f"  ·  Epoch {epoch}" if epoch else ""
        ax.set_title(f"Firing Rate  ·  {layer_name}{epoch_tag}", fontsize=9)

        fig.tight_layout(pad=0.8)
        path = ""
        if save:
            tag   = f"_epoch{epoch}" if epoch else ""
            fname = f"firing_rate_{layer_name.replace(' ', '_').lower()}{tag}.png"
            path  = os.path.join(self.output_dir, fname)
            fig.savefig(path)
            print(f"  ✓ Firing rate plot saved → {path}")
        plt.close(fig)
        return path

    # =========================================================================
    # 5.  EPOCH HEATMAP
    # =========================================================================
    def plot_epoch_heatmap(self, epoch_rates, layer_name="Output Layer",
                           neuron_labels=None, save=True):
        mat    = np.stack(epoch_rates, axis=0)
        E, N   = mat.shape
        labels = neuron_labels or ACTIVITY_LABELS

        fig_w = max(6.0, N * 0.38)
        fig_h = max(2.4, E * 0.34)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))

        im = ax.imshow(mat, cmap=_SIM_CMAP, vmin=0,
                       vmax=max(mat.max(), 0.01),
                       aspect="auto", interpolation="nearest")

        if N <= 24 and E <= 24:
            for r in range(E):
                for c in range(N):
                    val  = mat[r, c]
                    tcol = "white" if val > mat.max() * 0.6 else "black"
                    ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                            fontsize=5.5, color=tcol)

        ax.set_yticks(range(E))
        ax.set_yticklabels([f"E{i+1}" for i in range(E)], fontsize=6.5)

        if labels and len(labels) >= N:
            ax.set_xticks(range(N))
            ax.set_xticklabels(labels[:N], rotation=45, ha="right", fontsize=6.5)
        else:
            step = max(1, N // 8)
            ax.set_xticks(range(0, N, step))
            ax.set_xticklabels([f"N{i}" for i in range(0, N, step)], fontsize=7)

        ax.set_ylabel("Epoch", fontsize=8)
        ax.set_xlabel("Neuron", fontsize=8)
        ax.set_title(f"Firing Rate Evolution  ·  {layer_name}", fontsize=9)

        cbar = fig.colorbar(im, ax=ax, fraction=0.015, pad=0.02)
        cbar.set_label("Spikes / step", fontsize=7)
        cbar.ax.tick_params(labelsize=6.5)

        fig.tight_layout(pad=0.8)
        path = ""
        if save:
            fname = f"epoch_heatmap_{layer_name.replace(' ', '_').lower()}.png"
            path  = os.path.join(self.output_dir, fname)
            fig.savefig(path)
            print(f"  ✓ Epoch heatmap saved → {path}")
        plt.close(fig)
        return path

    # =========================================================================
    # 6.  COMBINED DASHBOARD
    # =========================================================================
    def plot_all(self, spk_out, mem_rec=None, spk_in=None,
                 layer_name="Output Layer", sample_idx=0, epoch=None,
                 neuron_labels=None, epoch_rates=None,
                 max_neurons=10, save=True):
        labels = neuron_labels or ACTIVITY_LABELS
        arr    = np.asarray(spk_out)
        if arr.ndim == 3:
            arr = arr[:, sample_idx, :]
        T, n_neurons = arr.shape
        n_show = min(max_neurons, n_neurons)
        rates  = arr.sum(0) / T
        winner = int(rates.argmax())

        if mem_rec is not None:
            mem = np.asarray(mem_rec)
            if mem.ndim == 3:
                mem = mem[:, sample_idx, :]
            mem_norm = np.zeros_like(mem[:, :n_show])
            for i in range(n_show):
                col = mem[:, i]
                lo, hi = col.min(), col.max()
                mem_norm[:, i] = (col - lo) / (hi - lo + 1e-9)
        else:
            mem_norm = np.zeros((T, n_show))
            for i in range(n_show):
                v = 0.0
                for t in range(T):
                    v = 0.9 * v + float(arr[t, i]) * 0.4
                    mem_norm[t, i] = min(v, 1.0)

        if spk_in is None:
            spk_in = np.zeros(T)
        spk_in = np.asarray(spk_in)
        if spk_in.ndim == 2:
            spk_in = spk_in[:, sample_idx]

        has_heatmap = epoch_rates is not None and len(epoch_rates) > 1
        n_cols      = 3 if has_heatmap else 2
        col_widths  = [2.8, 1.5, 2.0] if has_heatmap else [2.8, 1.5]

        fig = plt.figure(figsize=(sum(col_widths) * 2.2, 5.0))
        outer_gs = gridspec.GridSpec(1, n_cols, figure=fig,
                                     width_ratios=col_widths,
                                     wspace=0.40, left=0.08, right=0.97,
                                     top=0.88, bottom=0.12)

        # Column 0: LIF panel
        inner_gs = gridspec.GridSpecFromSubplotSpec(
            3, 1, subplot_spec=outer_gs[0],
            height_ratios=[0.7, 3.5, 0.7], hspace=0.06)

        ax_in   = fig.add_subplot(inner_gs[0])
        ax_volt = fig.add_subplot(inner_gs[1], sharex=ax_in)
        ax_out  = fig.add_subplot(inner_gs[2], sharex=ax_in)

        ax_in.set_facecolor("white")
        _draw_spike_ticks(ax_in, spk_in, color="black", lw=0.8)
        ax_in.set_ylim(0, 1); ax_in.set_yticks([])
        ax_in.set_ylabel("Input", fontsize=7)
        ax_in.tick_params(labelbottom=False)
        ax_in.spines["bottom"].set_visible(False)
        epoch_tag = f"  ·  Epoch {epoch}" if epoch else ""
        ax_in.set_title(f"{layer_name}{epoch_tag}", fontsize=8.5, pad=4)

        ax_volt.set_facecolor("#F5F8FC")
        offset_step = 1.05
        for i in range(n_show - 1, -1, -1):
            col = _TRACE_COLORS[i % len(_TRACE_COLORS)]
            ax_volt.plot(mem_norm[:, i] + i * offset_step,
                         color=col, lw=0.85, alpha=0.90,
                         label=labels[i] if i < len(labels) else f"N{i}")
        ax_volt.set_ylim(-0.3, n_show * offset_step + 0.2)
        ax_volt.set_yticks([]); ax_volt.set_ylabel("Voltage", fontsize=7)
        ax_volt.tick_params(labelbottom=False)
        ax_volt.spines["bottom"].set_visible(False)

        ax_out.set_facecolor("white")
        for i in range(n_show):
            t_sp = np.where(arr[:, i] > 0.5)[0]
            if t_sp.size:
                ax_out.plot(t_sp, np.ones_like(t_sp) * 0.5,
                            marker="+", ms=5, mew=0.9,
                            color=_TRACE_COLORS[i % len(_TRACE_COLORS)], ls="none")
        ax_out.set_ylim(0, 1); ax_out.set_yticks([])
        ax_out.set_ylabel("Spikes", fontsize=7)
        ax_out.set_xlabel("Timestep", fontsize=7.5)
        ax_out.xaxis.set_major_locator(ticker.MultipleLocator(max(1, T // 5)))
        ax_out.set_xlim(-0.5, T - 0.5)

        handles, lbs_leg = ax_volt.get_legend_handles_labels()
        ax_volt.legend(handles[::-1], lbs_leg[::-1],
                       loc="upper left", bbox_to_anchor=(1.01, 1.0),
                       fontsize=5.8, handlelength=1.2, borderpad=0.4,
                       frameon=False, title="Neuron", title_fontsize=6)

        # Column 1: firing rate bars
        ax_rate = fig.add_subplot(outer_gs[1])
        bar_colors = [_TRACE_COLORS[i % len(_TRACE_COLORS)] for i in range(n_neurons)]
        brs = ax_rate.barh(range(n_neurons), rates, color=bar_colors,
                           height=0.72, alpha=0.85, edgecolor="none")
        brs[winner].set_edgecolor("#333333")
        brs[winner].set_linewidth(0.9)

        if labels and len(labels) >= n_neurons:
            ax_rate.set_yticks(range(n_neurons))
            ax_rate.set_yticklabels(labels[:n_neurons], fontsize=5.8)
        else:
            step = max(1, n_neurons // 8)
            ax_rate.set_yticks(range(0, n_neurons, step))
            ax_rate.set_yticklabels([f"N{i}" for i in range(0, n_neurons, step)], fontsize=7)
        ax_rate.invert_yaxis()
        ax_rate.set_xlim(0, max(rates.max() * 1.25, 0.05))
        ax_rate.set_xlabel("Spikes / step", fontsize=7.5)
        ax_rate.set_title("Firing Rate", fontsize=8.5, pad=4)

        wlabel = labels[winner] if winner < len(labels) else f"N{winner}"
        ax_rate.text(0.97, 0.01, f"▶  {wlabel}",
                     transform=ax_rate.transAxes, ha="right", va="bottom",
                     fontsize=7, color="#333333", fontweight="bold")

        # Column 2 (optional): epoch heatmap
        if has_heatmap:
            mat = np.stack(epoch_rates, axis=0)
            E2, N2 = mat.shape
            ax_heat = fig.add_subplot(outer_gs[2])
            im = ax_heat.imshow(mat, cmap=_SIM_CMAP,
                                vmin=0, vmax=max(mat.max(), 0.01),
                                aspect="auto", interpolation="nearest")
            ax_heat.set_yticks(range(E2))
            ax_heat.set_yticklabels([f"E{i+1}" for i in range(E2)], fontsize=6)
            if labels and len(labels) >= N2:
                ax_heat.set_xticks(range(N2))
                ax_heat.set_xticklabels(labels[:N2], rotation=45,
                                        ha="right", fontsize=5.5)
            ax_heat.set_title("Rate Evolution", fontsize=8.5, pad=4)
            ax_heat.set_ylabel("Epoch", fontsize=7.5)
            ax_heat.set_xlabel("Neuron", fontsize=7.5)
            cbar = fig.colorbar(im, ax=ax_heat, fraction=0.04, pad=0.03)
            cbar.ax.tick_params(labelsize=6)
            cbar.set_label("Spikes/step", fontsize=6.5)

        path = ""
        if save:
            tag   = f"_epoch{epoch}" if epoch else ""
            fname = f"dashboard_{layer_name.replace(' ', '_').lower()}{tag}.png"
            path  = os.path.join(self.output_dir, fname)
            fig.savefig(path)
            print(f"  ✓ Dashboard saved → {path}")
        plt.close(fig)
        return path

    # ─────────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def save_spikes(spk, path):
        np.savez_compressed(path, spk_data=np.asarray(spk))
        print(f"  ✓ Spike data saved → {path}.npz")

    @staticmethod
    def load_spikes(path):
        return np.load(path)["spk_data"]

    @staticmethod
    def cosine_similarity_matrix(rate_vecs):
        N   = len(rate_vecs)
        mat = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                a, b  = np.asarray(rate_vecs[i]), np.asarray(rate_vecs[j])
                denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
                mat[i, j] = float(np.dot(a, b) / denom)
        return mat


# ─────────────────────────────────────────────────────────────────────────────
# Standalone demo
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file",  type=str, default=None)
    parser.add_argument("--layer", type=str, default="Output Layer")
    parser.add_argument("--epoch", type=int, default=None)
    parser.add_argument("--out",   type=str, default="spike_plots")
    args = parser.parse_args()

    viz = SpikeVisualizer(output_dir=args.out)

    if args.file:
        spk = SpikeVisualizer.load_spikes(args.file)
        viz.plot_all(spk, layer_name=args.layer, epoch=args.epoch,
                     neuron_labels=ACTIVITY_LABELS if spk.shape[-1] == 20 else None)
    else:
        print("Running demo with synthetic spike data …")
        rng = np.random.default_rng(0)
        T, batch, n_out = 30, 1, 20

        spk_demo = (rng.random((T, batch, n_out)) < 0.12).astype(np.float32)
        spk_demo[:, :, 3] = (rng.random((T, batch)) < 0.55).astype(np.float32)

        mem_demo = np.zeros_like(spk_demo)
        for i in range(n_out):
            v = 0.0
            for t in range(T):
                v = 0.9 * v + float(spk_demo[t, 0, i]) * 0.5
                mem_demo[t, 0, i] = min(v, 1.0)

        input_spk = (rng.random(T) < 0.15).astype(np.float32)

        epoch_rates = []
        for ep in range(1, 8):
            ep_spk = (rng.random((T, 1, n_out)) < 0.08 + ep * 0.01).astype(float)
            ep_spk[:, :, 3] = (rng.random((T, 1)) < 0.35 + ep * 0.03).astype(float)
            epoch_rates.append(ep_spk[:, 0, :].sum(0) / T)

        sim_mat = SpikeVisualizer.cosine_similarity_matrix(epoch_rates)
        names   = [f"E{i+1}" for i in range(len(epoch_rates))]

        viz.plot_lif_panel(spk_demo, mem_demo, input_spk,
                           neuron_labels=ACTIVITY_LABELS,
                           title="Single leaky integrate-and-fire neuron")
        viz.plot_raster(spk_demo, neuron_labels=ACTIVITY_LABELS)
        viz.plot_firing_rate(spk_demo, neuron_labels=ACTIVITY_LABELS)
        viz.plot_similarity_heatmap(sim_mat, names, title="Activity Similarity")
        viz.plot_epoch_heatmap(epoch_rates, neuron_labels=ACTIVITY_LABELS)
        viz.plot_all(spk_demo, mem_demo, input_spk,
                     neuron_labels=ACTIVITY_LABELS, epoch_rates=epoch_rates)

        print(f"\nAll demo plots written to: {args.out}/")
