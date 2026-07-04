"""Engine #4 — canonicalization tables for "Every Ball Ever" (R0).

Pure stdlib. Owns the corpus-exhaustive mappings for:
  * venue string  -> canonical ground (62 raw strings -> 37 grounds)
  * team string   -> canonical franchise name (renames unified; Gujarat
    Lions / Gujarat Titans / Gujarat Giants deliberately kept DISTINCT)
  * season label  -> canonical season int (slash labels normalized; every
    mapping is cross-checkable against dates[0] year — the corpus agrees
    1331/1331)
  * D/L flag from outcome.method
  * super-over innings detection (excluded from the point stream)

Every lookup raises KeyError on an unmapped input: the snapshot tests
assert the tables are exhaustive over the corpus, and a new Cricsheet
drop with a new venue/team string must fail loudly, never silently.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
OUT_ROOT = REPO_ROOT / "web" / "static" / "data"

LEAGUE_DIRS = (("ipl", "ipl_json"), ("wpl", "wpl_json"))

# ---------------------------------------------------------------------------
# Seasons
# ---------------------------------------------------------------------------

IPL_SEASONS = tuple(range(2008, 2027))  # 2008..2026 — 19 seasons
WPL_SEASONS = tuple(range(2023, 2027))  # 2023..2026 —  4 seasons

# Cricsheet slash-form season labels -> canonical year.
# The rule is "the year the cricket was actually played" (== dates[0] year
# for every match in the corpus): '2007/08' cricket was played in 2008,
# '2009/10' in 2010, but '2020/21' (the COVID UAE season) in 2020.
SEASON_LABELS = {
    "2007/08": 2008,
    "2009/10": 2010,
    "2020/21": 2020,
    "2022/23": 2023,
    "2023/24": 2024,
    "2024/25": 2025,
    "2025/26": 2026,
}


def canon_season(info: dict) -> int:
    """Canonical season year from a match's info block."""
    raw = str(info["season"])
    if raw in SEASON_LABELS:
        return SEASON_LABELS[raw]
    year = int(raw)  # plain-year labels ('2009', 2017, ...)
    if not (2008 <= year <= 2026):
        raise KeyError(f"unmapped season label: {raw!r}")
    return year


def season_from_dates(info: dict) -> int:
    """Independent derivation: the year of the match's first day of play."""
    return int(str(info["dates"][0])[:4])


# ---------------------------------------------------------------------------
# Teams / franchises
# ---------------------------------------------------------------------------

# Raw -> canonical. Franchise continuity renames only. Gujarat Lions (2016-17
# stand-in), Gujarat Titans (2022- IPL) and Gujarat Giants (WPL) are three
# different teams and are NOT unified. Deccan Chargers is not Sunrisers
# Hyderabad. 'Royal Challengers Bangalore' -> 'Bengaluru' applies in both
# leagues (both rebranded).
TEAM_RENAMES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}

# The complete canonical team universe of the corpus (17 names; Delhi
# Capitals / Mumbai Indians / Royal Challengers Bengaluru exist in both
# leagues — league context disambiguates, the name does not).
KNOWN_TEAMS = frozenset(
    {
        "Chennai Super Kings",
        "Deccan Chargers",
        "Delhi Capitals",
        "Gujarat Giants",
        "Gujarat Lions",
        "Gujarat Titans",
        "Kochi Tuskers Kerala",
        "Kolkata Knight Riders",
        "Lucknow Super Giants",
        "Mumbai Indians",
        "Pune Warriors",
        "Punjab Kings",
        "Rajasthan Royals",
        "Rising Pune Supergiant",
        "Royal Challengers Bengaluru",
        "Sunrisers Hyderabad",
        "UP Warriorz",
    }
)

# The 10 current IPL franchises + 5 WPL franchises used by the payoff cards.
CURRENT_IPL_FRANCHISES = (
    "Chennai Super Kings",
    "Delhi Capitals",
    "Gujarat Titans",
    "Kolkata Knight Riders",
    "Lucknow Super Giants",
    "Mumbai Indians",
    "Punjab Kings",
    "Rajasthan Royals",
    "Royal Challengers Bengaluru",
    "Sunrisers Hyderabad",
)
WPL_FRANCHISES = (
    "Delhi Capitals",
    "Gujarat Giants",
    "Mumbai Indians",
    "Royal Challengers Bengaluru",
    "UP Warriorz",
)


def canon_team(name: str) -> str:
    canonical = TEAM_RENAMES.get(name, name)
    if canonical not in KNOWN_TEAMS:
        raise KeyError(f"unmapped team: {name!r}")
    return canonical


# ---------------------------------------------------------------------------
# Venues
# ---------------------------------------------------------------------------

# All 62 raw venue strings in the corpus -> 37 canonical grounds.
# Same physical ground under sponsor/political renames is unified:
#   Feroz Shah Kotla == Arun Jaitley Stadium; Subrata Roy Sahara Stadium ==
#   MCA Stadium, Pune; Sardar Patel Stadium (Motera) == Narendra Modi
#   Stadium (same site, rebuilt); PCA Stadium == PCA IS Bindra Stadium;
#   Sheikh Zayed == Zayed Cricket Stadium.
VENUE_CANON = {
    "Arun Jaitley Stadium": "Arun Jaitley Stadium, Delhi",
    "Arun Jaitley Stadium, Delhi": "Arun Jaitley Stadium, Delhi",
    "Feroz Shah Kotla": "Arun Jaitley Stadium, Delhi",
    "Barabati Stadium": "Barabati Stadium, Cuttack",
    "Barsapara Cricket Stadium, Guwahati": "Barsapara Cricket Stadium, Guwahati",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow": "Ekana Cricket Stadium, Lucknow",
    "Brabourne Stadium": "Brabourne Stadium, Mumbai",
    "Brabourne Stadium, Mumbai": "Brabourne Stadium, Mumbai",
    "Buffalo Park": "Buffalo Park, East London",
    "De Beers Diamond Oval": "De Beers Diamond Oval, Kimberley",
    "Dr DY Patil Sports Academy": "Dr DY Patil Sports Academy, Navi Mumbai",
    "Dr DY Patil Sports Academy, Mumbai": "Dr DY Patil Sports Academy, Navi Mumbai",
    "Dr DY Patil Sports Academy, Navi Mumbai": "Dr DY Patil Sports Academy, Navi Mumbai",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium": "ACA-VDCA Cricket Stadium, Visakhapatnam",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam": "ACA-VDCA Cricket Stadium, Visakhapatnam",
    "Dubai International Cricket Stadium": "Dubai International Cricket Stadium, Dubai",
    "Eden Gardens": "Eden Gardens, Kolkata",
    "Eden Gardens, Kolkata": "Eden Gardens, Kolkata",
    "Green Park": "Green Park, Kanpur",
    "Himachal Pradesh Cricket Association Stadium": "HPCA Stadium, Dharamsala",
    "Himachal Pradesh Cricket Association Stadium, Dharamsala": "HPCA Stadium, Dharamsala",
    "Holkar Cricket Stadium": "Holkar Cricket Stadium, Indore",
    "JSCA International Stadium Complex": "JSCA International Stadium Complex, Ranchi",
    "Kingsmead": "Kingsmead, Durban",
    "Kotambi Stadium, Vadodara": "Kotambi Stadium, Vadodara",
    "M Chinnaswamy Stadium": "M Chinnaswamy Stadium, Bengaluru",
    "M Chinnaswamy Stadium, Bengaluru": "M Chinnaswamy Stadium, Bengaluru",
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium, Bengaluru",
    "MA Chidambaram Stadium": "MA Chidambaram Stadium, Chennai",
    "MA Chidambaram Stadium, Chepauk": "MA Chidambaram Stadium, Chennai",
    "MA Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium, Chennai",
    "Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur": "Maharaja Yadavindra Singh Stadium, Mullanpur",
    "Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh": "Maharaja Yadavindra Singh Stadium, Mullanpur",
    "Maharashtra Cricket Association Stadium": "MCA Stadium, Pune",
    "Maharashtra Cricket Association Stadium, Pune": "MCA Stadium, Pune",
    "Subrata Roy Sahara Stadium": "MCA Stadium, Pune",
    "Narendra Modi Stadium, Ahmedabad": "Narendra Modi Stadium, Ahmedabad",
    "Sardar Patel Stadium, Motera": "Narendra Modi Stadium, Ahmedabad",
    "Nehru Stadium": "Jawaharlal Nehru Stadium, Kochi",
    "New Wanderers Stadium": "Wanderers Stadium, Johannesburg",
    "Newlands": "Newlands, Cape Town",
    "OUTsurance Oval": "OUTsurance Oval, Bloemfontein",
    "Punjab Cricket Association IS Bindra Stadium": "PCA IS Bindra Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "PCA IS Bindra Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh": "PCA IS Bindra Stadium, Mohali",
    "Punjab Cricket Association Stadium, Mohali": "PCA IS Bindra Stadium, Mohali",
    "Rajiv Gandhi International Stadium": "Rajiv Gandhi International Stadium, Hyderabad",
    "Rajiv Gandhi International Stadium, Uppal": "Rajiv Gandhi International Stadium, Hyderabad",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": "Rajiv Gandhi International Stadium, Hyderabad",
    "Saurashtra Cricket Association Stadium": "SCA Stadium, Rajkot",
    "Sawai Mansingh Stadium": "Sawai Mansingh Stadium, Jaipur",
    "Sawai Mansingh Stadium, Jaipur": "Sawai Mansingh Stadium, Jaipur",
    "Shaheed Veer Narayan Singh International Stadium": "Shaheed Veer Narayan Singh Stadium, Raipur",
    "Shaheed Veer Narayan Singh International Stadium, Raipur": "Shaheed Veer Narayan Singh Stadium, Raipur",
    "Sharjah Cricket Stadium": "Sharjah Cricket Stadium, Sharjah",
    "Sheikh Zayed Stadium": "Zayed Cricket Stadium, Abu Dhabi",
    "Zayed Cricket Stadium, Abu Dhabi": "Zayed Cricket Stadium, Abu Dhabi",
    "St George's Park": "St George's Park, Port Elizabeth",
    "SuperSport Park": "SuperSport Park, Centurion",
    "Vidarbha Cricket Association Stadium, Jamtha": "VCA Stadium, Nagpur",
    "Wankhede Stadium": "Wankhede Stadium, Mumbai",
    "Wankhede Stadium, Mumbai": "Wankhede Stadium, Mumbai",
}

# Canonical ground -> city (host city; UAE/South Africa away seasons included).
GROUND_CITY = {
    "ACA-VDCA Cricket Stadium, Visakhapatnam": "Visakhapatnam",
    "Arun Jaitley Stadium, Delhi": "Delhi",
    "Barabati Stadium, Cuttack": "Cuttack",
    "Barsapara Cricket Stadium, Guwahati": "Guwahati",
    "Brabourne Stadium, Mumbai": "Mumbai",
    "Buffalo Park, East London": "East London",
    "De Beers Diamond Oval, Kimberley": "Kimberley",
    "Dr DY Patil Sports Academy, Navi Mumbai": "Navi Mumbai",
    "Dubai International Cricket Stadium, Dubai": "Dubai",
    "Eden Gardens, Kolkata": "Kolkata",
    "Ekana Cricket Stadium, Lucknow": "Lucknow",
    "Green Park, Kanpur": "Kanpur",
    "HPCA Stadium, Dharamsala": "Dharamsala",
    "Holkar Cricket Stadium, Indore": "Indore",
    "JSCA International Stadium Complex, Ranchi": "Ranchi",
    "Jawaharlal Nehru Stadium, Kochi": "Kochi",
    "Kingsmead, Durban": "Durban",
    "Kotambi Stadium, Vadodara": "Vadodara",
    "M Chinnaswamy Stadium, Bengaluru": "Bengaluru",
    "MA Chidambaram Stadium, Chennai": "Chennai",
    "MCA Stadium, Pune": "Pune",
    "Maharaja Yadavindra Singh Stadium, Mullanpur": "New Chandigarh",
    "Narendra Modi Stadium, Ahmedabad": "Ahmedabad",
    "Newlands, Cape Town": "Cape Town",
    "OUTsurance Oval, Bloemfontein": "Bloemfontein",
    "PCA IS Bindra Stadium, Mohali": "Mohali",
    "Rajiv Gandhi International Stadium, Hyderabad": "Hyderabad",
    "SCA Stadium, Rajkot": "Rajkot",
    "Sawai Mansingh Stadium, Jaipur": "Jaipur",
    "Shaheed Veer Narayan Singh Stadium, Raipur": "Raipur",
    "Sharjah Cricket Stadium, Sharjah": "Sharjah",
    "St George's Park, Port Elizabeth": "Port Elizabeth",
    "SuperSport Park, Centurion": "Centurion",
    "VCA Stadium, Nagpur": "Nagpur",
    "Wanderers Stadium, Johannesburg": "Johannesburg",
    "Wankhede Stadium, Mumbai": "Mumbai",
    "Zayed Cricket Stadium, Abu Dhabi": "Abu Dhabi",
}


def canon_venue(raw: str) -> str:
    try:
        return VENUE_CANON[raw]
    except KeyError:
        raise KeyError(f"unmapped venue: {raw!r}") from None


# ---------------------------------------------------------------------------
# Match / innings flags
# ---------------------------------------------------------------------------


def is_dl(info: dict) -> bool:
    """True when the result came via Duckworth/Lewis (outcome.method)."""
    method = info.get("outcome", {}).get("method")
    return bool(method) and "D/L" in method


def is_super_over(innings: dict) -> bool:
    """Super-over innings are excluded from the point stream (standing rule)."""
    return bool(innings.get("super_over"))
