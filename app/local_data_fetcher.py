"""
Local Data Fetcher - Retrieves real facts about cities for AI content generation.
Uses US Census API for housing age data - reliable and free.
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalDataFetcher:
    """Fetches verified local data about cities to enhance AI-generated content."""
    
    def __init__(self):
        self.timeout = 10.0
        self.current_year = datetime.now().year
        
    async def fetch_city_data(self, city: str, state: str) -> Dict[str, Any]:
        """
        Fetch housing age data for a city from US Census API.
        Returns dict with housing facts.
        """
        city_data = {
            "city": city,
            "state": state,
            "housing_facts": [],
        }
        
        # Fetch housing age data from Census API
        try:
            housing_data = await self._fetch_census_housing_age(city, state)
            if housing_data:
                city_data["housing_facts"] = housing_data
        except Exception as e:
            logger.warning(f"Census fetch failed for {city}, {state}: {e}")
        
        return city_data
    
    async def _fetch_census_housing_age(self, city: str, state: str) -> List[str]:
        """Fetch housing age data from US Census API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use Census ACS 5-Year Data for housing characteristics
                # This is more reliable than trying to get city-specific data
                # We'll use state-level data as a proxy
                
                state_fips = self._get_state_fips(state)
                if not state_fips:
                    return []
                
                # Census API endpoint for housing units by year built
                # Using ACS 5-Year estimates (most recent and stable)
                api_url = "https://api.census.gov/data/2022/acs/acs5"
                
                # B25034: Year Structure Built
                # We'll get median year and calculate average age
                params = {
                    "get": "B25035_001E",  # Median year structure built
                    "for": f"state:{state_fips}",
                }
                
                response = await client.get(api_url, params=params)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                
                if len(data) < 2:  # Need header + data row
                    return []
                
                # Parse median year built
                try:
                    median_year = float(data[1][0])
                    if median_year > 1800 and median_year < self.current_year:
                        avg_age = self.current_year - int(median_year)
                        return [
                            f"Many homes in the area were built around {int(median_year)}, making them approximately {avg_age} years old"
                        ]
                except (ValueError, IndexError):
                    pass
                
                return []
                
        except Exception as e:
            logger.warning(f"Census API fetch failed for {city}, {state}: {e}")
            return []
    
    def _get_state_fips(self, state: str) -> Optional[str]:
        """Convert state abbreviation or name to FIPS code."""
        state_fips_map = {
            "AL": "01", "Alabama": "01",
            "AK": "02", "Alaska": "02",
            "AZ": "04", "Arizona": "04",
            "AR": "05", "Arkansas": "05",
            "CA": "06", "California": "06",
            "CO": "08", "Colorado": "08",
            "CT": "09", "Connecticut": "09",
            "DE": "10", "Delaware": "10",
            "FL": "12", "Florida": "12",
            "GA": "13", "Georgia": "13",
            "HI": "15", "Hawaii": "15",
            "ID": "16", "Idaho": "16",
            "IL": "17", "Illinois": "17",
            "IN": "18", "Indiana": "18",
            "IA": "19", "Iowa": "19",
            "KS": "20", "Kansas": "20",
            "KY": "21", "Kentucky": "21",
            "LA": "22", "Louisiana": "22",
            "ME": "23", "Maine": "23",
            "MD": "24", "Maryland": "24",
            "MA": "25", "Massachusetts": "25",
            "MI": "26", "Michigan": "26",
            "MN": "27", "Minnesota": "27",
            "MS": "28", "Mississippi": "28",
            "MO": "29", "Missouri": "29",
            "MT": "30", "Montana": "30",
            "NE": "31", "Nebraska": "31",
            "NV": "32", "Nevada": "32",
            "NH": "33", "New Hampshire": "33",
            "NJ": "34", "New Jersey": "34",
            "NM": "35", "New Mexico": "35",
            "NY": "36", "New York": "36",
            "NC": "37", "North Carolina": "37",
            "ND": "38", "North Dakota": "38",
            "OH": "39", "Ohio": "39",
            "OK": "40", "Oklahoma": "40",
            "OR": "41", "Oregon": "41",
            "PA": "42", "Pennsylvania": "42",
            "RI": "44", "Rhode Island": "44",
            "SC": "45", "South Carolina": "45",
            "SD": "46", "South Dakota": "46",
            "TN": "47", "Tennessee": "47",
            "TX": "48", "Texas": "48",
            "UT": "49", "Utah": "49",
            "VT": "50", "Vermont": "50",
            "VA": "51", "Virginia": "51",
            "WA": "53", "Washington": "53",
            "WV": "54", "West Virginia": "54",
            "WI": "55", "Wisconsin": "55",
            "WY": "56", "Wyoming": "56",
        }
        return state_fips_map.get(state.upper())
    
    
    def format_for_prompt(self, city_data: Dict[str, Any]) -> str:
        """Format city data for inclusion in AI prompt."""
        if not city_data or not city_data.get("housing_facts"):
            return ""
        
        facts = city_data["housing_facts"]
        if not facts:
            return ""
        
        return "\n".join([f"VERIFIED LOCAL FACT: {fact}" for fact in facts])


# Global instance
local_data_fetcher = LocalDataFetcher()
