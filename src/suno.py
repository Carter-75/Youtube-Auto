"""
Suno API Integration for Lo-Fi Music Generation
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
    """Handle Suno API music generation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.suno.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(tries=3, delay=5, backoff=2)
    def generate_music(self, prompt: str, duration: int = 120) -> Dict:
        """
        Generate lo-fi music using Suno API
        
        Args:
            prompt: Text description of the music to generate
            duration: Length of track in seconds (default 120 = 2 minutes)
        
        Returns:
            Dictionary with generation_id and other metadata
        """
        logger.info(f"Generating music with prompt: {prompt}")
        
        payload = {
            "prompt": prompt,
            "duration": duration,
            "instrumental": True,
            "genre": "lofi"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            generation_id = data.get("id")
            
            if not generation_id:
                raise ValueError("No generation ID returned from Suno API")
            
            logger.info(f"Music generation started. ID: {generation_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate music: {e}")
            raise
    
    @retry(tries=10, delay=10, backoff=1.5)
    def wait_for_completion(self, generation_id: str) -> Dict:
        """
        Poll Suno API until music generation is complete
        
        Args:
            generation_id: ID of the generation task
        
        Returns:
            Complete generation data including audio URL
        """
        logger.info(f"Waiting for generation {generation_id} to complete...")
        
        try:
            response = requests.get(
                f"{self.base_url}/generate/{generation_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            logger.info(f"Generation status: {status}")
            
            if status == "completed":
                logger.info("Music generation completed!")
                return data
            elif status == "failed":
                raise Exception(f"Music generation failed: {data.get('error', 'Unknown error')}")
            else:
                # Still processing, raise to trigger retry
                raise Exception("Generation still in progress")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check generation status: {e}")
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
            duration: Track duration in seconds
        
        Returns:
            Path to downloaded audio file
        """
        # Start generation
        generation_data = self.generate_music(prompt, duration)
        generation_id = generation_data.get("id")
        
        # Wait for completion
        completed_data = self.wait_for_completion(generation_id)
        
        # Get audio URL
        audio_url = completed_data.get("audio_url")
        if not audio_url:
            raise ValueError("No audio URL in completed generation data")
        
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

