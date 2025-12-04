from ytmusicapi import YTMusic
from typing import List, Optional
import logging
from models import Track

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YTMusicClient:
    """Robust YouTube Music API wrapper"""
    
    def __init__(self):
        """Initialize client"""
        try:
            self.client = YTMusic()
            logger.info("✓ YouTube Music client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize YTMusic: {e}")
            raise

    def search_songs(self, query: str, limit: int = 20) -> List[Track]:
 
        tracks: List[Track] = []
        
        try:
            # Clamp limit to API constraints
            api_limit = max(1, min(limit, 100))  # YouTube Music API max is usually 20-100
            
            logger.info(f"Searching: query='{query}', limit={api_limit}")
            
            # Try with filter parameter
            try:
                results = self.client.search(
                    query=query,
                    filter="songs",
                    limit=api_limit
                )
            except TypeError:
                # Fallback for older versions
                logger.warning("Filter parameter not supported, using fallback")
                results = self.client.search(query=query, limit=api_limit)
                results = [r for r in results if r.get("resultType") == "song"]
            
            logger.info(f"API returned {len(results)} results")
            
            # Parse results
            for item in results:
                try:
                    track = self._parse_track(item)
                    if track and track.video_id:
                        tracks.append(track)
                        
                        # CRITICAL: Stop when we reach limit
                        if len(tracks) >= limit:
                            logger.info(f"Reached limit of {limit} tracks, stopping")
                            break
                            
                except Exception as e:
                    logger.warning(f"Failed to parse item: {e}")
                    continue
            
            logger.info(f"✓ Returning {len(tracks)} valid tracks (requested: {limit})")
            
        except Exception as e:
            logger.error(f"✗ Search failed: {e}")
        
        return tracks

    def _parse_track(self, item: dict) -> Optional[Track]:
        """Parse API response into Track object"""
        try:
            # Extract title
            title = item.get("title") or item.get("name") or "Unknown Title"
            
            # Extract artist/channel
            channel = "Unknown Artist"
            artists = item.get("artists") or []
            if isinstance(artists, list) and artists:
                try:
                    channel = artists[0].get("name", "Unknown Artist")
                except (IndexError, AttributeError, TypeError):
                    pass
            elif item.get("author"):
                channel = item.get("author")
            
            # Extract duration
            duration = item.get("duration") or item.get("length") or "0:00"
            if not duration or duration == "None":
                duration = "0:00"
            
            # Extract video ID - CRITICAL
            video_id = (
                item.get("videoId") or 
                item.get("browseId") or 
                item.get("id") or 
                ""
            )
            
            if not video_id:
                logger.debug("No video_id found, skipping")
                return None
            
            # Extract thumbnail
            thumbnail = None
            thumbnails = item.get("thumbnails", [])
            if isinstance(thumbnails, list) and thumbnails:
                try:
                    thumbnail = thumbnails[-1].get("url")
                except (IndexError, AttributeError, TypeError):
                    pass
            
            # Build URL
            url = f"https://music.youtube.com/watch?v={video_id}"
            
            return Track(
                title=title.strip(),
                channel=channel.strip(),
                duration=duration,
                video_id=video_id,
                thumbnail=thumbnail,
                url=url,
                result_type=item.get("resultType", "song")
            )
            
        except Exception as e:
            logger.error(f"Parse track error: {e}")
            return None

    def get_track_info(self, video_id: str) -> Optional[Track]:
        """Get detailed track information"""
        try:
            result = self.client.get_song(video_id)
            if isinstance(result, dict):
                video_details = result.get("videoDetails", {})
                if video_details:
                    return self._parse_track(video_details)
            return None
        except Exception as e:
            logger.error(f"get_track_info failed: {e}")
            return None

    def __repr__(self) -> str:
        return "YTMusicClient(ready)"