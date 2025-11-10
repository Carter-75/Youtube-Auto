"""
Main Orchestration Script for Automated Lo-Fi YouTube Channel

WINDOWS ONLY - This project is designed for Windows operating systems
"""
import os
import sys
import json
import time
import logging
import platform
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import our modules
from suno import SunoAPI, create_lofi_prompt
from openai_gen import OpenAIGenerator
from youtube_upload import YouTubeUploader
from wake_lock import WakeLock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LoFiAutomation:
    """Main automation orchestrator"""
    
    def __init__(self):
        """Initialize automation with API clients"""
        load_dotenv()
        
        # Load API keys
        self.suno_key = os.getenv('COMET_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.youtube_client_id = os.getenv('YOUTUBE_CLIENT_ID')
        self.youtube_client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        self.youtube_refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
        
        # Validate API keys
        self._validate_env_vars()
        
        # Initialize API clients
        logger.info("Initializing API clients...")
        self.suno = SunoAPI(self.suno_key)
        self.openai = OpenAIGenerator(self.openai_key)
        self.youtube = YouTubeUploader(
            self.youtube_client_id,
            self.youtube_client_secret,
            self.youtube_refresh_token
        )
        
        # Create directory structure
        self.base_dir = Path(__file__).parent.parent
        self.audio_dir = self.base_dir / 'audio'
        self.thumbnail_dir = self.base_dir / 'thumbnails'
        self.metadata_dir = self.base_dir / 'metadata'
        
        for directory in [self.audio_dir, self.thumbnail_dir, self.metadata_dir]:
            directory.mkdir(exist_ok=True)
        
        logger.info("Automation system initialized successfully!")
    
    def _validate_env_vars(self):
        """Validate that all required environment variables are set"""
        required_vars = {
            'COMET_API_KEY': self.suno_key,
            'OPENAI_API_KEY': self.openai_key,
            'YOUTUBE_CLIENT_ID': self.youtube_client_id,
            'YOUTUBE_CLIENT_SECRET': self.youtube_client_secret
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value or value.startswith('your_')]
        
        if missing_vars:
            logger.error(f"Missing or invalid environment variables: {', '.join(missing_vars)}")
            logger.error("Please check your .env file and add valid API keys")
            sys.exit(1)
    
    def generate_timestamp_id(self) -> str:
        """Generate unique timestamp-based ID"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def check_duplicate(self, timestamp_id: str) -> bool:
        """Check if a video with this timestamp already exists"""
        metadata_file = self.metadata_dir / f'metadata_{timestamp_id}.json'
        return metadata_file.exists()
    
    def create_video_from_audio(self, audio_path: str, output_path: str, thumbnail_path: str):
        """
        Create a simple video file from audio and thumbnail image
        Uses ffmpeg to create a static image video
        
        Args:
            audio_path: Path to audio file
            output_path: Path for output video
            thumbnail_path: Path to thumbnail image
        """
        import subprocess
        
        logger.info("Creating video file from audio and thumbnail...")
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg not found. Installing ffmpeg-python...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'ffmpeg-python'], check=True)
        
        # Create video with static image and audio
        command = [
            'ffmpeg',
            '-loop', '1',
            '-i', thumbnail_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-y',  # Overwrite output file
            output_path
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            logger.info(f"Video created successfully: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create video: {e.stderr.decode()}")
            raise
    
    def run_pipeline(self, custom_prompt: str = None) -> Dict:
        """
        Execute complete automation pipeline
        Wake lock is acquired during execution to prevent system sleep
        
        Args:
            custom_prompt: Optional custom music generation prompt
        
        Returns:
            Dictionary with all generated data and upload info
        """
        timestamp_id = self.generate_timestamp_id()
        
        # Check for duplicates
        if self.check_duplicate(timestamp_id):
            logger.warning(f"Duplicate detected for {timestamp_id}, skipping...")
            return None
        
        logger.info("="*70)
        logger.info(f"Starting new lo-fi video generation pipeline: {timestamp_id}")
        logger.info("="*70)
        
        # Acquire wake lock to prevent system sleep during generation
        wake_lock = WakeLock("LoFiAutomation-Pipeline")
        wake_lock.acquire()
        
        try:
            # STEP 1: Generate music prompt
            if custom_prompt:
                music_prompt = custom_prompt
            else:
                music_prompt = create_lofi_prompt()
            
            logger.info(f"Music prompt: {music_prompt}")
            
            # STEP 2: Generate and download music
            audio_path = self.audio_dir / f'lofi_{timestamp_id}.mp3'
            logger.info("Step 1/6: Generating lo-fi music...")
            self.suno.generate_and_download(music_prompt, str(audio_path), duration=120)
            
            # STEP 3: Generate metadata and thumbnail prompt
            logger.info("Step 2/6: Generating video metadata...")
            thumbnail_path = self.thumbnail_dir / f'thumb_{timestamp_id}.png'
            metadata = self.openai.generate_complete_assets(music_prompt, str(thumbnail_path))
            
            logger.info("Step 3/6: Thumbnail generated!")
            
            # STEP 4: Create video from audio and thumbnail
            logger.info("Step 4/6: Creating video file...")
            video_path = self.audio_dir / f'video_{timestamp_id}.mp4'
            self.create_video_from_audio(str(audio_path), str(video_path), str(thumbnail_path))
            
            # STEP 5: Upload to YouTube
            logger.info("Step 5/6: Uploading to YouTube...")
            upload_result = self.youtube.upload_complete_video(
                video_path=str(video_path),
                thumbnail_path=str(thumbnail_path),
                metadata=metadata,
                privacy_status="private"
            )
            
            # STEP 6: Save metadata locally
            logger.info("Step 6/6: Saving metadata...")
            complete_metadata = {
                'timestamp_id': timestamp_id,
                'music_prompt': music_prompt,
                'audio_path': str(audio_path),
                'video_path': str(video_path),
                'thumbnail_path': str(thumbnail_path),
                'title': metadata['title'],
                'description': metadata['description'],
                'tags': metadata['tags'],
                'thumbnail_prompt': metadata['thumbnail_prompt'],
                'video_id': upload_result['video_id'],
                'video_url': upload_result['video_url'],
                'upload_timestamp': datetime.now().isoformat(),
                'privacy_status': 'private'
            }
            
            metadata_path = self.metadata_dir / f'metadata_{timestamp_id}.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(complete_metadata, f, indent=2, ensure_ascii=False)
            
            logger.info("="*70)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Video ID: {upload_result['video_id']}")
            logger.info(f"Video URL: {upload_result['video_url']}")
            logger.info(f"Metadata saved to: {metadata_path}")
            logger.info("="*70)
            
            return complete_metadata
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
        finally:
            # Always release wake lock when pipeline finishes (success or failure)
            wake_lock.release()
    
    def run_multiple(self, count: int, delay_seconds: int = 60):
        """
        Run pipeline multiple times
        Wake lock is released during delays to allow system sleep
        
        Args:
            count: Number of videos to generate
            delay_seconds: Delay between generations to avoid rate limits
        """
        logger.info(f"Starting batch generation of {count} videos...")
        
        successful = 0
        failed = 0
        
        for i in range(count):
            logger.info(f"\n{'='*70}")
            logger.info(f"Generating video {i+1} of {count}")
            logger.info(f"{'='*70}\n")
            
            try:
                # run_pipeline() handles its own wake lock
                self.run_pipeline()
                successful += 1
                
                if i < count - 1:  # Don't delay after last video
                    # Wake lock is automatically released by run_pipeline()
                    # System can sleep during delay period
                    logger.info(f"[SLEEP] Waiting {delay_seconds} seconds before next generation...")
                    logger.info(f"System can sleep during this delay period")
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                logger.error(f"Video {i+1} failed: {e}")
                failed += 1
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Batch generation complete!")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"{'='*70}\n")


def main():
    """Main entry point"""
    # Check if running on Windows
    if platform.system() != "Windows":
        print("=" * 60)
        print("ERROR: This project only supports Windows")
        print(f"Detected OS: {platform.system()}")
        print("=" * 60)
        sys.exit(1)
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   Automated Lo-Fi YouTube Channel Generator              ║
    ║   Powered by Suno + OpenAI + YouTube API                 ║
    ║   WINDOWS ONLY                                           ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        automation = LoFiAutomation()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--loop':
                count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
                delay = int(sys.argv[3]) if len(sys.argv) > 3 else 60
                automation.run_multiple(count, delay)
            else:
                print("Usage:")
                print("  python main.py              # Generate one video")
                print("  python main.py --loop 5     # Generate 5 videos")
                print("  python main.py --loop 5 120 # Generate 5 videos with 120s delay")
        else:
            # Single video generation
            automation.run_pipeline()
        
    except KeyboardInterrupt:
        logger.info("\nAutomation stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

