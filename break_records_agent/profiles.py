from dataclasses import dataclass
from typing import Tuple, List

@dataclass
class DemographicProfile:
    key: str
    label: str
    age_range: str
    genres: Tuple[str, ...]
    mood: str

PROFILES = [
    DemographicProfile(
        key="gen_z_rnb",
        label="Gen Z R&B / Pop",
        age_range="18-24",
        genres=("R&B", "Pop", "Hip Hop"),
        mood="Aesthetic, emotional, nostalgic",
    ),
    DemographicProfile(
        key="millennial_indie",
        label="Millennial Indie",
        age_range="25-34",
        genres=("Indie Rock", "Alternative"),
        mood="Atmospheric, moody, authentic",
    ),
    DemographicProfile(
        key="hype_rap",
        label="Hype Rap / Trap",
        age_range="16-24",
        genres=("Rap", "Trap"),
        mood="High energy, flex, confident",
    ),
    DemographicProfile(
        key="pop_country",
        label="Pop Country",
        age_range="25-45",
        genres=("Country", "Pop Country"),
        mood="Storytelling, heartfelt, rustic",
    ),
]

def list_profiles() -> List[DemographicProfile]:
    return PROFILES

def get_profile(key: str) -> DemographicProfile:
    for p in PROFILES:
        if p.key == key:
            return p
    return PROFILES[0]
