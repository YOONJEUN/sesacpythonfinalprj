import koreanize_matplotlib  # noqa: F401
import matplotlib.pyplot as plt
import pandas as pd


CATEGORY_ORDER = [
    "\uc9c0\ud558\ucca0/\ubc84\uc2a4", "\uc8fc\uac70\uc9c0", "\uae30\ud0c0", "\uacf5\uacf5\uae30\uad00", "\ud68c\uc0ac",
    "\uacf5\uc6d0", "\ucd08\uc911\uace0", "\ub300\ud559\uad50", "\ubb38\ud654\uc2dc\uc124",
]

PATTERNS = [
    ("\uc9c0\ud558\ucca0/\ubc84\uc2a4", r"\uc5ed|\ubc84\uc2a4|\uc815\ub958\uc7a5|\ud130\ubbf8\ub110|\uacf5\ud56d|\uad50\ud1b5|\ud658\uc2b9"),
    ("\ub300\ud559\uad50", r"\ub300\ud559\uad50|\ub300\ud559|\ucea0\ud37c\uc2a4|\ub300\ud559\uc6d0"),
    ("\ucd08\uc911\uace0", r"\ucd08\ub4f1|\uc911\ud559\uad50|\uace0\ub4f1|\ud559\uad50|\uc720\uce58\uc6d0"),
    ("\uacf5\uc6d0", r"\uacf5\uc6d0|\ud55c\uac15|\ud638\uc218|\uc0b0|\uc22b|\uc0dd\ud0dc|\uc218\ubcc0"),
    ("\ubb38\ud654\uc2dc\uc124", r"\ubb38\ud654|\ubbf8\uc220|\ubc15\ubb3c|\uacf5\uc5f0|\uc608\uc220|\uc601\ud654|\uadf9\uc7a5|\ubbf8\ub514\uc5b4|\ub514\uc790\uc778|\uc5ed\uc0ac|\uc804\uc2dc"),
    ("\uacf5\uacf5\uae30\uad00", r"\uad6c\uccad|\uc8fc\ubbfc\uc13c\ud130|\ubcf4\uac74\uc18c|\uacbd\ucc30|\uc18c\ubc29|\uc6b0\uccb4\uad6d|\uc2dc\uccad|\uad50\uc721\uccad|\uc138\ubb34|\ubc95\uc6d0|\ud589\uc815|\ubcf5\uc9c0|\uacf5\ub2e8"),
    ("\ud68c\uc0ac", r"\ud68c\uc0ac|\ube4c\ub529|\ud0c0\uc6cc|\uc0ac\uc625|\ubcf8\uc0ac|\uc9c0\uc810|KT|SK|LG|\uc0bc\uc131|\ud604\ub300|GS|\uc740\ud589|\uae08\uc735|\ubc29\uc1a1|\uc5f0\uad6c\uc18c"),
    ("\uc8fc\uac70\uc9c0", r"\uc544\ud30c\ud2b8|APT|\uc790\uc774|\ub798\ubbf8\uc548|\ud478\ub974\uc9c0\uc624|\ud790\uc2a4\ud14c\uc774\ud2b8|\uc544\uc774\ud30c\ud06c|\uc8fc\uacf5|\ube4c\ub77c|\uc8fc\ud0dd"),
]


def classify_station_names(names: pd.Series) -> pd.Series:
    result = pd.Series("\uae30\ud0c0", index=names.index, dtype="string")
    normalized = names.fillna("").astype("string")
    for category, pattern in PATTERNS:
        matches = normalized.str.contains(pattern, case=False, regex=True, na=False)
        result = result.mask(matches & result.eq("\uae30\ud0c0"), category)
    return result


def add_station_categories(rental_df: pd.DataFrame) -> pd.DataFrame:
    result = rental_df.copy()
    result["rent_category"] = classify_station_names(result["rent_nm"])
    result["rtn_category"] = classify_station_names(result["rtn_nm"])
    return result


def calculate_hourly_category_imbalance(categorized_df: pd.DataFrame) -> pd.DataFrame:
    rentals = categorized_df.groupby(["rent_hour", "rent_category"]).size().rename("rentals")
    returns = categorized_df.dropna(subset=["rtn_hour"]).groupby(["rtn_hour", "rtn_category"]).size().rename("returns")
    index = pd.MultiIndex.from_product([range(24), CATEGORY_ORDER], names=["hour", "category"])
    result = pd.concat([rentals, returns], axis=1).reindex(index, fill_value=0).fillna(0).reset_index()
    result["imbalance"] = result["rentals"] - result["returns"]
    return result


def create_hourly_category_imbalance_chart(hourly_df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(13, 6))
    for category in CATEGORY_ORDER:
        data = hourly_df.loc[hourly_df["category"].eq(category)]
        ax.plot(data["hour"], data["imbalance"], marker="o", linewidth=2, label=category)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(range(24))
    ax.set_xlabel("\uc2dc\uac04\ub300")
    ax.set_ylabel("\ubd88\uade0\ud615 \uc218\uce58 (\ub300\uc5ec \uac74\uc218 - \ubc18\ub0a9 \uac74\uc218)")
    ax.set_title("\ub300\uc5ec\uc18c \uc720\ud615\ubcc4 \uc2dc\uac04\ub300 \ubd88\uade0\ud615 \ucd94\uc774 (2026\ub144 4\uc6d4 1\uc77c~7\uc77c)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="\ub300\uc5ec\uc18c \uc720\ud615", ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    fig.tight_layout()
    return fig

# Rebind after declarations so Arrow-backed string columns receive real Unicode regexes.
def classify_station_names(names: pd.Series) -> pd.Series:
    result = pd.Series("\uae30\ud0c0", index=names.index, dtype="string")
    normalized = names.fillna("").astype("string")
    for category, pattern in PATTERNS:
        resolved_pattern = pattern.encode("utf-8").decode("unicode_escape")
        matches = normalized.str.contains(resolved_pattern, case=False, regex=True, na=False)
        result = result.mask(matches & result.eq("\uae30\ud0c0"), category)
    return result
