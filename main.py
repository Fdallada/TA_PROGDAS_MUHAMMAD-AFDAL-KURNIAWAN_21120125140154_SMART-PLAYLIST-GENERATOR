import sys
import os
import logging
from tkinter import messagebox
import tkinter as tk

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
from ytm_client import YTMusicClient
from recommender import RecommenderEngine
from gui import SmartPlaylistGUI


def create_directories():
    """Create necessary directories"""
    directories = ["data", "data/cache", "data/saved_playlists"]
    for d in directories:
        try:
            os.makedirs(d, exist_ok=True)
            logger.info(f"✓ Directory: {d}")
        except Exception as e:
            logger.error(f"Failed to create {d}: {e}")


def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("SmartPlaylist Premium - Starting")
    logger.info("="*60)

    # Create directories
    create_directories()

    # Initialize YouTube Music client
    ytm = None
    try:
        ytm = YTMusicClient()
        logger.info("✓ YouTube Music client initialized")
    except Exception as e:
        logger.warning(f"⚠ YTMusic init failed: {e}")
        logger.info("Running in fallback mode")

    # Initialize recommender
    try:
        engine = RecommenderEngine(ytm)
        logger.info("✓ Recommender engine initialized")
    except Exception as e:
        logger.critical(f"✗ Recommender init failed: {e}")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Failed to initialize:\n{e}")
        root.destroy()
        sys.exit(1)

    # Start GUI
    try:
        logger.info("Starting GUI...")
        app = SmartPlaylistGUI(recommender=engine, ytm_client=ytm)
        app.run()
    except Exception as e:
        logger.critical(f"✗ GUI error: {e}", exc_info=True)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("GUI Error", f"Failed to start GUI:\n{e}")
            root.destroy()
        except:
            pass
        sys.exit(1)

    logger.info("Application closed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)