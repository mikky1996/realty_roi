import pandas as pd
import typing as tp
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from io import BytesIO
from . import metric_units


def get_report(
    input_summary: str,
    df: pd.DataFrame,
    return_as_stream: bool = False
) -> tp.Optional[BytesIO]:
    """
    Plot all metrics from a DataFrame with an input summary.
    :param input_summary: Description of the project
    :param df: Data about profitability
    :param return_as_stream: Should return a bytestream?
    :return: None or bytestream
    """

    metrics = [col for col in df.columns if col != "Year"]
    num_metrics = len(metrics)

    cols = 2
    rows = (num_metrics + 1) // cols + ((num_metrics + 1) % cols > 0)
    fig, axes = plt.subplots(rows, cols, figsize=(14, rows * 3), constrained_layout=True)
    axes = axes.flatten()  # Flatten the grid for easier indexing

    # Add input summary
    axes[0].axis('off')  # Turn off the plot for the input summary
    axes[0].text(0.5, 0.5, input_summary, fontsize=12, ha='center', va='center', multialignment='left')
    axes[0].set_title("Input Summary", fontsize=16, weight='bold')

    # Define color palette and markers
    colors = plt.cm.tab10.colors
    markers = ['o', 's', 'D', '^', 'x', '*', 'p', 'H']

    # Plot each metric
    for i, metric in enumerate(metrics, start=1):
        ax = axes[i]
        ax.plot(
            df['Year'],
            df[metric],
            label=metric,
            marker=markers[i % len(markers)],
            color=colors[i % len(colors)],
            linewidth=2
        )
        ax.set_title(metric, fontsize=14, weight='bold')
        ax.set_xlabel("Year", fontsize=12)
        unit = metric_units.get(metric, "")
        ax.set_ylabel(f"Value ({unit})", fontsize=12)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        ax.legend(fontsize=10)

        # Format Y-axis
        if unit == "USD":
            ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
        elif unit == "%":
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())

    # Hide unused subplots
    for i in range(len(metrics) + 1, len(axes)):
        axes[i].axis('off')

    # Save to byte stream if required
    # Returns a bytestream pdf
    if return_as_stream:
        buf = BytesIO()
        plt.savefig(buf, format='pdf', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    # Display the plots
    plt.show()
