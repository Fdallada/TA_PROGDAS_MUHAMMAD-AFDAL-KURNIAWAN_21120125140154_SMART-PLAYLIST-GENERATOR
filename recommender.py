import logging
from typing import Optional, Tuple, List
from models import Playlist, Track

logger = logging.getLogger(__name__)


class RecommenderEngine:
    """Intelligent playlist recommendation engine"""
    
    def __init__(self, ytm_client=None):
        """Initialize recommender"""
        self.yt = ytm_client
        self._fallback_mode = ytm_client is None
        
        if self._fallback_mode:
            logger.warning("⚠ Recommender in fallback mode")
        else:
            logger.info("✓ Recommender initialized")

    def generate(
        self,
        mood: str,
        activity: str,
        time_of_day: str,
        genre: Optional[str] = None,
        top_n: int = 10
    ) -> Tuple[Optional[Playlist], str]:
        """
        Generate smart playlist with EXACT track count
        
        Args:
            mood: User's mood
            activity: Current activity
            time_of_day: Time of day
            genre: Optional music genre
            top_n: EXACT number of tracks to return
            
        Returns:
            Tuple of (Playlist or None, search_query)
        """
        # Validate inputs
        if not mood or not activity or not time_of_day:
            logger.error("Missing required parameters")
            return None, ""
        
        # Clamp top_n to reasonable limits
        top_n = max(5, min(top_n, 50))
        
        # Build query
        query = self._build_query(mood, activity, time_of_day, genre)
        logger.info(f"🎵 Generating playlist: query='{query}', count={top_n}")
        
        # Fallback mode
        if self._fallback_mode or not self.yt:
            logger.warning("No YouTube Music client available")
            return None, query
        
        # Search tracks - request MORE than needed for deduplication
        try:
            # CRITICAL FIX: Request 2x tracks for deduplication buffer
            search_limit = top_n * 2
            logger.info(f"Searching with limit={search_limit} (will return {top_n})")
            
            results = self.yt.search_songs(query=query, limit=search_limit)
            
            if not results:
                logger.warning(f"No results found for query: '{query}'")
                return None, query
            
            logger.info(f"Found {len(results)} raw results")
            
            # Deduplicate by video_id
            unique_tracks = self._deduplicate_tracks(results)
            logger.info(f"After deduplication: {len(unique_tracks)} unique tracks")
            
            # CRITICAL FIX: Select EXACTLY top_n tracks
            selected_tracks = unique_tracks[:top_n]
            logger.info(f"Selected EXACTLY {len(selected_tracks)} tracks (requested: {top_n})")
            
            # Create playlist
            playlist_name = self._generate_playlist_name(mood, activity, time_of_day, genre)
            playlist = Playlist(name=playlist_name, tracks=selected_tracks)
            
            logger.info(f"✓ Generated playlist: '{playlist_name}' with {len(selected_tracks)} tracks")
            
            # Verify count matches
            if len(selected_tracks) != top_n:
                logger.warning(f"⚠ Track count mismatch! Expected {top_n}, got {len(selected_tracks)}")
            
            return playlist, query
            
        except Exception as e:
            logger.error(f"✗ Playlist generation failed: {e}")
            return None, query

    def _build_query(
        self,
        mood: str,
        activity: str,
        time_of_day: str,
        genre: Optional[str] = None
    ) -> str:
        """Build optimized search query"""
        parts = []
        
        # Add non-empty parts
        for part in [mood, activity, time_of_day]:
            if part and part.strip():
                parts.append(part.strip().lower())
        
        # Add genre if provided
        if genre and genre.strip():
            parts.append(genre.strip().lower())
        
        # Add "music" keyword
        parts.append("music")
        
        return " ".join(parts)

    def _deduplicate_tracks(self, tracks: List[Track]) -> List[Track]:
        """Remove duplicate tracks by video_id"""
        seen_ids = set()
        unique = []
        
        for track in tracks:
            if not track.video_id:
                continue
            
            if track.video_id not in seen_ids:
                seen_ids.add(track.video_id)
                unique.append(track)
        
        logger.info(f"Deduplication: {len(tracks)} -> {len(unique)} tracks")
        return unique

    def _generate_playlist_name(
        self,
        mood: str,
        activity: str,
        time_of_day: str,
        genre: Optional[str] = None
    ) -> str:
        """Generate descriptive playlist name"""
        parts = []
        
        if mood:
            parts.append(mood.title())
        if time_of_day:
            parts.append(time_of_day.title())
        if activity:
            parts.append(activity.title())
        if genre:
            parts.append(genre.title())
        
        base_name = " ".join(parts) if parts else "My Playlist"
        return f"{base_name} Mix"

    def is_ready(self) -> bool:
        """Check if recommender is ready"""
        return not self._fallback_mode and self.yt is not None

    def __repr__(self) -> str:
        mode = "fallback" if self._fallback_mode else "active"
        return f"RecommenderEngine(mode={mode})"