import io
import base64
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns

# Color constants to match Tailwind config
BG_COLOR = "#1a1d26"      # panel background
LINE_COLOR = "#2b2f3c"    # borders/grid lines
TEXT_MUTED = "#b7bccb"    # labels/ticks (ink.300)
TEXT_LIGHT = "#f4f5f7"    # titles (ink.100)
PANEL2_COLOR = "#20232e"  # legend background

# High quality vibrant color palette matching the application colors
COLOR_PALETTE = ["#f2b84b", "#38bdf8", "#818cf8", "#fb7185", "#34d399", "#a855f7"]


def apply_theme():
    """Applies modern dark-mode style variables to Matplotlib/Seaborn."""
    plt.rcParams["figure.facecolor"] = BG_COLOR
    plt.rcParams["axes.facecolor"] = BG_COLOR
    plt.rcParams["axes.edgecolor"] = LINE_COLOR
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.color"] = LINE_COLOR
    plt.rcParams["grid.linestyle"] = ":"
    plt.rcParams["xtick.color"] = TEXT_MUTED
    plt.rcParams["ytick.color"] = TEXT_MUTED
    plt.rcParams["text.color"] = TEXT_MUTED
    plt.rcParams["axes.labelcolor"] = TEXT_LIGHT
    plt.rcParams["axes.titlecolor"] = TEXT_LIGHT
    plt.rcParams["legend.facecolor"] = PANEL2_COLOR
    plt.rcParams["legend.edgecolor"] = LINE_COLOR
    plt.rcParams["font.family"] = "sans-serif"
    sns.set_palette(COLOR_PALETTE)


def fig_to_base64_dict(fig) -> dict:
    """Converts a matplotlib figure to a base64 encoded image dictionary and closes the figure."""
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=140, facecolor=fig.get_facecolor())
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        return {"type": "image", "src": f"data:image/png;base64,{img_str}"}
    finally:
        plt.close(fig)


def histogram(df: pd.DataFrame, column: str) -> dict:
    """Generates a styled histplot using Seaborn."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(data=df, x=column, kde=True, ax=ax)
    ax.set_title(f"Distribution of {column}")
    return fig_to_base64_dict(fig)


def boxplot(df: pd.DataFrame, column: str) -> dict:
    """Generates a styled boxplot using Seaborn."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df, x=column, ax=ax)
    ax.set_title(f"Distribution of {column}")
    return fig_to_base64_dict(fig)


def kdeplot(df: pd.DataFrame, column: str) -> dict:
    """Generates a styled KDE plot using Seaborn."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.kdeplot(data=df, x=column, fill=True, ax=ax)
    ax.set_title(f"KDE Plot of {column}")
    return fig_to_base64_dict(fig)


def count_plot(df: pd.DataFrame, column: str, top_n: int = 15) -> dict:
    """Generates a styled count plot using Seaborn."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 5))
    order = df[column].value_counts().iloc[:top_n].index
    sns.countplot(data=df, x=column, order=order, ax=ax)
    ax.set_title(f"Count Plot of {column}")
    plt.xticks(rotation=45, ha="right")
    return fig_to_base64_dict(fig)


def pie_chart(df: pd.DataFrame, column: str) -> dict:
    """Generates a styled pie chart using Matplotlib."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 5))
    counts = df[column].value_counts().head(8)
    ax.pie(counts.values, labels=counts.index.astype(str), autopct="%1.1f%%", 
           textprops={"color": TEXT_LIGHT})
    ax.set_title(f"Pie Chart of {column}")
    return fig_to_base64_dict(fig)


def correlation_heatmap(df: pd.DataFrame, method: str = "pearson") -> dict | None:
    """Generates a styled correlation heatmap using Seaborn."""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        return None
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 6))
    corr = numeric_df.corr(method=method)
    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, fmt=".2f", ax=ax)
    ax.set_title(f"{method.title()} Correlation Heatmap")
    return fig_to_base64_dict(fig)


def missing_values_chart(df: pd.DataFrame) -> dict:
    """Generates a styled bar plot of missing value percentages using Matplotlib."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 5))
    missing_pct = (df.isna().sum() / len(df) * 100).sort_values(ascending=False)
    missing_pct = missing_pct[missing_pct > 0]
    
    if missing_pct.empty:
        ax.text(0.5, 0.5, "No missing values detected", ha="center", va="center", color=TEXT_MUTED, fontsize=12)
        ax.set_axis_off()
        return fig_to_base64_dict(fig)
        
    sns.barplot(x=missing_pct.index.astype(str), y=missing_pct.values, ax=ax)
    ax.set_title("Missing Values (%) by Column")
    plt.xticks(rotation=45, ha="right")
    ax.set_ylabel("Percentage (%)")
    return fig_to_base64_dict(fig)


def generate_custom_plot(df: pd.DataFrame, columns: list[str], plot_type: str, params: dict = None) -> dict | None:
    """Routes customizable plotting tasks dynamically using Matplotlib and Seaborn."""
    apply_theme()
    params = params.copy() if params else {}
    if "hue" in params and params["hue"] not in df.columns:
        params["hue"] = None
    if "size" in params and params["size"] not in df.columns:
        params["size"] = None
    
    # Filter columns to only those that exist in df
    valid_cols = [c for c in columns if c in df.columns]
    if not valid_cols:
        return None
        
    plot_df = df.copy()
    
    # Handle high cardinality date-like columns by bucketing by Year-Month
    for col in valid_cols:
        if plot_df[col].dtype == "object" and plot_df[col].nunique() > 50:
            try:
                dt_series = pd.to_datetime(plot_df[col])
                if dt_series.nunique() > 50:
                    plot_df[col] = dt_series.dt.strftime('%Y-%m')
            except Exception:
                pass
                
    fig, ax = plt.subplots(figsize=(8, 5))
    plot_type = plot_type.lower().strip()
    
    try:
        if plot_type in ["histplot", "histogram"]:
            col = valid_cols[0]
            kde = params.get("kde", True)
            sns.histplot(data=plot_df, x=col, kde=kde, ax=ax)
            ax.set_title(f"Histogram of {col}")
            
        elif plot_type == "boxplot":
            if len(valid_cols) >= 2:
                x_col, y_col = valid_cols[0], valid_cols[1]
                # Swap columns if necessary for better boxplot orientation
                if plot_df[x_col].dtype == "object" or plot_df[x_col].nunique() < 10:
                    sns.boxplot(data=plot_df, x=x_col, y=y_col, hue=params.get("hue"), ax=ax)
                else:
                    sns.boxplot(data=plot_df, x=y_col, y=x_col, hue=params.get("hue"), ax=ax)
                ax.set_title(f"Boxplot of {y_col} by {x_col}")
            else:
                col = valid_cols[0]
                sns.boxplot(data=plot_df, x=col, ax=ax)
                ax.set_title(f"Boxplot of {col}")
                
        elif plot_type == "violinplot":
            if len(valid_cols) >= 2:
                x_col, y_col = valid_cols[0], valid_cols[1]
                if plot_df[x_col].dtype == "object" or plot_df[x_col].nunique() < 10:
                    sns.violinplot(data=plot_df, x=x_col, y=y_col, hue=params.get("hue"), ax=ax)
                else:
                    sns.violinplot(data=plot_df, x=y_col, y=x_col, hue=params.get("hue"), ax=ax)
                ax.set_title(f"Violin Plot of {y_col} by {x_col}")
            else:
                col = valid_cols[0]
                sns.violinplot(data=plot_df, x=col, ax=ax)
                ax.set_title(f"Violin Plot of {col}")
                
        elif plot_type == "kdeplot":
            col = valid_cols[0]
            sns.kdeplot(data=plot_df, x=col, fill=True, ax=ax)
            ax.set_title(f"KDE Plot of {col}")
            
        elif plot_type in ["countplot", "count_plot"]:
            col = valid_cols[0]
            hue = params.get("hue")
            top_n = params.get("top_n", 10)
            order = plot_df[col].value_counts().index[:top_n]
            sns.countplot(data=plot_df, x=col, order=order, hue=hue, ax=ax)
            ax.set_title(f"Count Plot of {col}")
            plt.xticks(rotation=45, ha="right")
            
        elif plot_type in ["pie", "pie_chart"]:
            col = valid_cols[0]
            counts = plot_df[col].value_counts().head(8)
            ax.pie(counts.values, labels=counts.index.astype(str), autopct="%1.1f%%", 
                   textprops={"color": TEXT_LIGHT})
            ax.set_title(f"Distribution of {col}")
            
        elif plot_type in ["scatterplot", "scatter"]:
            if len(valid_cols) >= 2:
                x_col, y_col = valid_cols[0], valid_cols[1]
                hue = params.get("hue")
                size = params.get("size")
                sns.scatterplot(data=plot_df, x=x_col, y=y_col, hue=hue, size=size, ax=ax)
                ax.set_title(f"Scatter Plot of {y_col} vs {x_col}")
            else:
                plt.close(fig)
                return None
                
        elif plot_type in ["lineplot", "line"]:
            if len(valid_cols) >= 2:
                x_col, y_col = valid_cols[0], valid_cols[1]
                hue = params.get("hue")
                
                # Use errorbar=None to speed up lineplot for large datasets
                if int(matplotlib.__version__.split(".")[0]) >= 3 and int(sns.__version__.split(".")[1]) >= 12:
                    sns.lineplot(data=plot_df, x=x_col, y=y_col, hue=hue, ax=ax, errorbar=None)
                else:
                    sns.lineplot(data=plot_df, x=x_col, y=y_col, hue=hue, ax=ax, ci=None)
                ax.set_title(f"Line Plot of {y_col} vs {x_col}")
            else:
                plt.close(fig)
                return None
                
        elif plot_type in ["barplot", "bar"]:
            if len(valid_cols) >= 2:
                x_col, y_col = valid_cols[0], valid_cols[1]
                hue = params.get("hue")
                sns.barplot(data=plot_df, x=x_col, y=y_col, hue=hue, ax=ax)
                ax.set_title(f"Bar Plot of {y_col} by {x_col}")
                plt.xticks(rotation=45, ha="right")
            else:
                plt.close(fig)
                return None
                
        elif plot_type == "heatmap":
            if len(valid_cols) >= 2:
                numeric_df = plot_df[valid_cols].select_dtypes(include="number")
                if numeric_df.shape[1] >= 2:
                    corr = numeric_df.corr()
                    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, ax=ax, fmt=".2f")
                    ax.set_title("Correlation Heatmap")
                else:
                    plt.close(fig)
                    return None
            else:
                plt.close(fig)
                return None
                
        elif plot_type == "pairplot":
            plt.close(fig)  # pairplot creates its own figure
            hue = params.get("hue")
            sub_cols = valid_cols[:4]
            
            # Form clean plotting dataframe
            if hue and hue in plot_df.columns and hue not in sub_cols:
                pair_df = plot_df[sub_cols + [hue]].dropna()
            else:
                pair_df = plot_df[sub_cols].dropna()
                
            pair_grid = sns.pairplot(data=pair_df, vars=sub_cols, hue=hue, plot_kws={"alpha": 0.6})
            pair_grid.fig.patch.set_facecolor(BG_COLOR)
            
            for ax_sub in pair_grid.axes.flat:
                if ax_sub is not None:
                    ax_sub.set_facecolor(BG_COLOR)
                    for spine in ax_sub.spines.values():
                        spine.set_color(LINE_COLOR)
                    ax_sub.xaxis.label.set_color(TEXT_LIGHT)
                    ax_sub.yaxis.label.set_color(TEXT_LIGHT)
                    ax_sub.tick_params(colors=TEXT_MUTED)
                    
            return fig_to_base64_dict(pair_grid.fig)
            
        else:
            col = valid_cols[0]
            sns.histplot(data=plot_df, x=col, ax=ax)
            ax.set_title(f"Distribution of {col}")
            
        return fig_to_base64_dict(fig)
        
    except Exception as e:
        plt.close(fig)
        from loguru import logger
        logger.error(f"Error generating {plot_type} plot for columns {columns}: {e}")
        return None
