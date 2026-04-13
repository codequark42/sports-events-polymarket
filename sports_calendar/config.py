from __future__ import annotations

from dataclasses import dataclass


TIMEZONE_NAME = "Europe/Rome"
POLYMARKET_BASE_URL = "https://gamma-api.polymarket.com"
POLYMARKET_WEB_BASE_URL = "https://polymarket.com"
SPORTS_TAG_ID = 1
DEFAULT_F1_ICS_URL = (
    "https://ics.ecal.com/ecal-sub/69c26447d1780a00029628bd/Formula%201.ics"
)

DEFAULT_DAYS_FORWARD = 240
DEFAULT_DAYS_BACK = 30
DEFAULT_PAGE_LIMIT = 100
DEFAULT_MAX_POLYMARKET_PAGES = 8
DEFAULT_CACHE_TTL_SECONDS = 300
DEFAULT_HTTP_TIMEOUT_SECONDS = 60
DEFAULT_HTTP_RETRIES = 3

SOCCER_TAGS = {
    "soccer",
    "epl",
    "la liga",
    "serie a",
    "bundesliga",
    "ligue 1",
    "champions league",
    "ucl",
    "europa league",
    "uel",
    "fa cup",
    "coppa italia",
    "dfb pokal",
    "copa del rey",
    "efl championship",
    "games",
}
MAJOR_SOCCER_COMPETITIONS = {
    "epl",
    "la liga",
    "serie a",
    "bundesliga",
    "ligue 1",
    "champions league",
    "ucl",
    "europa league",
    "uel",
    "fa cup",
    "coppa italia",
    "dfb pokal",
    "copa del rey",
    "uefa europa league",
}
SOCCER_KNOCKOUT_KEYWORDS = {
    "semi-final",
    "semifinal",
    "semi final",
    "final",
    "quarter-final",
    "quarterfinal",
}
SOCCER_TITLE_DECIDER_KEYWORDS = {
    "title decider",
    "winner takes all",
    "decider",
}
BIG_SOCCER_TEAMS = {
    "arsenal",
    "aston villa",
    "atalanta",
    "athletic club",
    "atletico madrid",
    "atlético madrid",
    "barcelona",
    "bayer leverkusen",
    "bayern münchen",
    "bayern munich",
    "borussia dortmund",
    "chelsea",
    "inter",
    "inter milan",
    "juventus",
    "lazio",
    "liverpool",
    "manchester city",
    "manchester united",
    "milan",
    "monaco",
    "marseille",
    "napoli",
    "newcastle united",
    "paris saint-germain",
    "psg",
    "real madrid",
    "real sociedad",
    "rb leipzig",
    "roma",
    "sporting cp",
    "tottenham",
    "porto",
}

UFC_TAGS = {"ufc", "mma"}
UFC_EXCLUDED_KEYWORDS = {
    "fight next",
    "champion at the end of",
    "pound-for-pound",
    "pound for pound",
    "who will become",
    "who will be",
}
CURRENT_TOP_UFC_FIGHTER_KEYWORDS = {"islam makhachev", "makhachev"}

CHESS_KEYWORDS = {
    "hikaru",
    "nakamura",
    "magnus",
    "carlsen",
    "world championship",
    "world chess championship",
}

TENNIS_TAGS = {"tennis", "atp", "wta", "roland garros"}
TENNIS_PLAYER_KEYWORDS = {"djokovic", "novak", "sinner", "alcaraz", "carlos alcaraz"}
TENNIS_ROUND_KEYWORDS = {"semi-final", "semifinal", "semi final", "final"}
GRAND_SLAM_KEYWORDS = {
    "australian open",
    "roland garros",
    "french open",
    "wimbledon",
    "us open",
    "grand slam",
}

VALORANT_TAGS = {"valorant", "vct", "champions tour"}
BIG_VALORANT_TEAMS = {
    "100 thieves",
    "drx",
    "edward gaming",
    "edg",
    "fnatic",
    "g2 esports",
    "gen.g",
    "heretics",
    "leviatan",
    "leviatán",
    "loud",
    "nrg",
    "paper rex",
    "prx",
    "sentinels",
    "team heretics",
}

CRICKET_TAGS = {"cricket", "ipl", "t20", "indian premier league"}
CRICKET_TARGET_TEAMS = {
    "india",
    "royal challengers bengaluru",
    "royal challengers bangalore",
    "rcb",
    "delhi capitals",
}
CRICKET_KNOCKOUT_KEYWORDS = {
    "semi-final",
    "semifinal",
    "semi final",
    "final",
    "qualifier",
    "eliminator",
    "playoff",
    "knockout",
}

F1_RACE_SUFFIXES = {" - race", " - sprint"}

FOOTBALL_LEAGUE_PAGE_ROUTES = {
    "/sports/epl/games": "EPL",
    "/sports/laliga/games": "La Liga",
    "/sports/sea/games": "Serie A",
    "/sports/bundesliga/games": "Bundesliga",
    "/sports/ligue-1/games": "Ligue 1",
}
FOOTBALL_CUP_PAGE_ROUTES = {
    "/sports/ucl/games": "UEFA Champions League",
    "/sports/uel/games": "UEFA Europa League",
    "/sports/fa-cup/games": "FA Cup",
    "/sports/cdr/games": "Copa del Rey",
    "/sports/dfb/games": "DFB Pokal",
    "/sports/itc/games": "Coppa Italia",
}
FOOTBALL_PAGE_ROUTES = {
    **FOOTBALL_LEAGUE_PAGE_ROUTES,
    **FOOTBALL_CUP_PAGE_ROUTES,
}
UFC_PAGE_ROUTE = "/sports/ufc/games"
CHESS_PAGE_ROUTE = "/sports/chess/games"
TENNIS_PAGE_ROUTES = {
    "/sports/atp/games": "ATP",
    "/sports/wta/games": "WTA",
}
CRICKET_PAGE_ROUTES = {
    "/sports/cricipl/games": "IPL",
    "/sports/crint/games": "International Cricket",
}
VALORANT_PAGE_ROUTE = "/esports/valorant/games"


@dataclass(frozen=True)
class BuildOptions:
    days_forward: int = DEFAULT_DAYS_FORWARD
    days_back: int = DEFAULT_DAYS_BACK
    max_polymarket_pages: int = DEFAULT_MAX_POLYMARKET_PAGES
    page_limit: int = DEFAULT_PAGE_LIMIT
    f1_ics_url: str = DEFAULT_F1_ICS_URL
