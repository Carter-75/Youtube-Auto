"""
CometAPI Integration for Lo-Fi Music Generation (Suno Music API)
CometAPI provides unofficial access to Suno's music generation capabilities
"""
import os
import time
import requests
import logging
from typing import Dict, Optional
from retry import retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SunoAPI:
    """Handle CometAPI music generation using Suno AI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.cometapi.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(tries=3, delay=5, backoff=2)
    def generate_music(self, prompt: str, duration: int = 120) -> Dict:
        """
        Generate lo-fi music using CometAPI (Suno)
        
        Args:
            prompt: Text description of the music to generate
            duration: Length of track in seconds (default 120 = 2 minutes)
        
        Returns:
            Dictionary with generation data
        """
        logger.info(f"Generating music with prompt: {prompt}")
        
        payload = {
            "prompt": prompt,
            "make_instrumental": True,
            "wait_audio": True,
            "tags": "lofi, study music, chill beats"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/custom_generate",
                headers=self.headers,
                json=payload,
                timeout=180  # CometAPI can take longer with wait_audio=True
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'data' not in data:
                raise ValueError("Invalid response from CometAPI")
            
            logger.info(f"Music generation completed successfully")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate music: {e}")
            raise
    
    @retry(tries=3, delay=5, backoff=2)
    def download_audio(self, audio_url: str, output_path: str) -> str:
        """
        Download generated audio file
        
        Args:
            audio_url: URL of the generated audio
            output_path: Local path to save the audio file
        
        Returns:
            Path to downloaded file
        """
        logger.info(f"Downloading audio from: {audio_url}")
        
        try:
            response = requests.get(audio_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Audio downloaded successfully to: {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download audio: {e}")
            raise
    
    def generate_and_download(self, prompt: str, output_path: str, duration: int = 120) -> str:
        """
        Complete workflow: generate music and download it
        
        Args:
            prompt: Music generation prompt
            output_path: Where to save the audio file
            duration: Track duration in seconds (note: actual duration controlled by Suno)
        
        Returns:
            Path to downloaded audio file
        """
        # Generate music
        result_data = self.generate_music(prompt, duration)
        
        # Extract audio URL from response
        # CometAPI returns data in format: {"data": [{"audio_url": "..."}]}
        if 'data' in result_data and len(result_data['data']) > 0:
            audio_url = result_data['data'][0].get('audio_url')
            if not audio_url:
                raise ValueError("No audio URL in response data")
        else:
            raise ValueError("Invalid response structure from CometAPI")
        
        # Download audio
        return self.download_audio(audio_url, output_path)


def create_lofi_prompt() -> str:
    """
    Generate a randomized lo-fi music prompt
    
    Returns:
        A descriptive prompt for lo-fi music generation
    """
    import random
    
    tempos = ["80 BPM", "85 BPM", "90 BPM", "75 BPM"]
    ambiences = [
        "soft rain ambience",
        "gentle cafe background",
        "quiet library atmosphere",
        "peaceful nature sounds",
        "subtle vinyl crackle"
    ]
    instruments = [
        "calming synth pads",
        "mellow piano keys",
        "warm bass lines",
        "jazzy guitar chords",
        "smooth rhodes piano"
    ]
    moods = [
        "study focus",
        "late night relaxation",
        "peaceful meditation",
        "creative flow",
        "chill vibes"
    ]
    
    tempo = random.choice(tempos)
    ambience = random.choice(ambiences)
    instrument = random.choice(instruments)
    mood = random.choice(moods)
    
    prompt = f"Lofi study music, {tempo}, {ambience}, {instrument}, {mood}"
    return prompt
