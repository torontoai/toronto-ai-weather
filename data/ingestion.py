"""
Data ingestion module for Toronto AI Weather.

This module handles fetching data from various sources and storing it in the database.
"""

import logging
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy.orm import Session
from toronto_ai_weather.config.config import DATA_SOURCES
from toronto_ai_weather.data.db import WeatherData, get_db

# Set up logging
logger = logging.getLogger(__name__)

class DataIngestionManager:
    """Manager class for data ingestion from multiple sources."""
    
    def __init__(self):
        self.sources = DATA_SOURCES
        self.ingestors = {
            'weather_stations': {
                'noaa': NOAAIngestor(),
                'eccc': ECCCIngestor(),
            },
            'satellite': {
                'nasa': NASAIngestor(),
            },
            'social_media': {
                'twitter': TwitterIngestor(),
            },
        }
    
    async def ingest_all(self):
        """Ingest data from all configured sources."""
        tasks = []
        
        for category, sources in self.ingestors.items():
            for source_name, ingestor in sources.items():
                if source_name in self.sources.get(category, {}):
                    config = self.sources[category][source_name]
                    tasks.append(ingestor.ingest(config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error during ingestion: {result}")
    
    async def schedule_ingestion(self):
        """Schedule periodic ingestion based on update intervals."""
        while True:
            await self.ingest_all()
            await asyncio.sleep(60)  # Check every minute for sources that need updating


class BaseIngestor:
    """Base class for data ingestors."""
    
    async def ingest(self, config: Dict[str, Any]) -> None:
        """Ingest data from the source and store it in the database."""
        raise NotImplementedError("Subclasses must implement this method")
    
    async def fetch_data(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Fetch data from a URL."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching data from {url}: {response.status}")
                        return {}
            except Exception as e:
                logger.error(f"Exception fetching data from {url}: {e}")
                return {}
    
    def store_data(self, source: str, location: str, data: Dict[str, Any]) -> None:
        """Store data in the database."""
        try:
            db = next(get_db())
            weather_data = WeatherData(
                timestamp=datetime.utcnow(),
                source=source,
                location=location,
                data=data
            )
            db.add(weather_data)
            db.commit()
            logger.info(f"Stored data from {source} for {location}")
        except Exception as e:
            logger.error(f"Error storing data from {source} for {location}: {e}")


class NOAAIngestor(BaseIngestor):
    """Ingestor for NOAA weather data."""
    
    async def ingest(self, config: Dict[str, Any]) -> None:
        """Ingest data from NOAA API."""
        try:
            # Get list of stations
            stations_data = await self.fetch_data(config['api_url'])
            if not stations_data:
                return
            
            # Get data for each station
            for station in stations_data.get('features', [])[:10]:  # Limit to 10 stations for now
                station_id = station['properties']['stationIdentifier']
                station_url = f"{config['api_url']}/{station_id}/observations/latest"
                station_data = await self.fetch_data(station_url)
                
                if station_data:
                    # Extract relevant data
                    properties = station_data.get('properties', {})
                    processed_data = {
                        'temperature': properties.get('temperature', {}).get('value'),
                        'humidity': properties.get('relativeHumidity', {}).get('value'),
                        'windSpeed': properties.get('windSpeed', {}).get('value'),
                        'windDirection': properties.get('windDirection', {}).get('value'),
                        'barometricPressure': properties.get('barometricPressure', {}).get('value'),
                        'visibility': properties.get('visibility', {}).get('value'),
                        'textDescription': properties.get('textDescription'),
                    }
                    
                    # Store in database
                    self.store_data('noaa', station_id, processed_data)
        
        except Exception as e:
            logger.error(f"Error in NOAA ingestion: {e}")


class ECCCIngestor(BaseIngestor):
    """Ingestor for Environment and Climate Change Canada (ECCC) weather data."""
    
    async def ingest(self, config: Dict[str, Any]) -> None:
        """Ingest data from ECCC API."""
        try:
            # For now, just focus on Toronto
            city_id = 'on-143'
            city_url = f"{config['api_url']}/{city_id}_e.xml"
            
            # ECCC provides XML, so we need to handle it differently
            async with aiohttp.ClientSession() as session:
                async with session.get(city_url) as response:
                    if response.status == 200:
                        # Parse XML (simplified for now)
                        xml_text = await response.text()
                        # In a real implementation, use proper XML parsing
                        # For now, just store the raw XML
                        self.store_data('eccc', city_id, {'raw_xml': xml_text[:1000]})  # Truncate for demo
                    else:
                        logger.error(f"Error fetching ECCC data: {response.status}")
        
        except Exception as e:
            logger.error(f"Error in ECCC ingestion: {e}")


class NASAIngestor(BaseIngestor):
    """Ingestor for NASA satellite data."""
    
    async def ingest(self, config: Dict[str, Any]) -> None:
        """Ingest data from NASA API."""
        try:
            # Focus on Toronto area
            params = {
                'lon': -79.3832,
                'lat': 43.6532,
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'api_key': config['api_key'],
            }
            
            # Construct URL with parameters
            url = f"{config['api_url']}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            
            data = await self.fetch_data(url)
            if data:
                self.store_data('nasa', 'toronto', data)
        
        except Exception as e:
            logger.error(f"Error in NASA ingestion: {e}")


class TwitterIngestor(BaseIngestor):
    """Ingestor for Twitter (X) data for sentiment analysis."""
    
    async def ingest(self, config: Dict[str, Any]) -> None:
        """Ingest data from Twitter API."""
        try:
            # Set up authentication
            headers = {
                'Authorization': f"Bearer {config['api_key']}",
            }
            
            # Search for weather-related tweets in Toronto
            params = {
                'query': 'weather toronto',
                'max_results': 100,
            }
            
            url = f"{config['api_url']}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            
            data = await self.fetch_data(url, headers)
            if data:
                # Process tweets for sentiment analysis
                tweets = data.get('data', [])
                processed_data = {
                    'tweet_count': len(tweets),
                    'tweets': tweets[:10],  # Store only first 10 tweets for demo
                }
                
                self.store_data('twitter', 'toronto', processed_data)
        
        except Exception as e:
            logger.error(f"Error in Twitter ingestion: {e}")


# Main function to run the ingestion process
async def run_ingestion():
    """Run the data ingestion process."""
    manager = DataIngestionManager()
    await manager.schedule_ingestion()

if __name__ == "__main__":
    asyncio.run(run_ingestion())
