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
        Uses the correct endpoint structure: submit task, then poll for completion
        
        Args:
            prompt: Text description of the music to generate
            duration: Length of track in seconds (default 120 = 2 minutes)
        
        Returns:
            Dictionary with generation data including audio URL
        """
        logger.info(f"Generating music with prompt: {prompt}")
        
        # Generate a simple title based on timestamp
        from datetime import datetime
        title = f"Lo-Fi Study Music {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Use inspiration mode with gpt_description_prompt for instrumental
        payload = {
            "gpt_description_prompt": prompt,
            "mv": "chirp-auk",  # Suno v4.5
            "prompt": "",
            "make_instrumental": True,
            "title": title,
            "tags": "lofi, study music, chill beats"
        }
        
        try:
            # Step 1: Submit the music generation task
            logger.info("Submitting music generation task to CometAPI...")
            response = requests.post(
                f"{self.base_url}/suno/submit/music",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Check response before raising for status
            if response.status_code != 200:
                try:
                    error_detail = response.json()
                    logger.error(f"API Error Response: {error_detail}")
                except:
                    logger.error(f"API Error Response (raw): {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') != 'success' or not result.get('data'):
                raise ValueError(f"Task submission failed: {result}")
            
            task_id = result['data']
            logger.info(f"Task submitted successfully. Task ID: {task_id}")
            
            # Step 2: Poll for completion
            logger.info("Waiting for music generation to complete...")
            max_attempts = 60  # 5 minutes max (60 * 5 seconds)
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                time.sleep(5)  # Wait 5 seconds between polls
                
                fetch_response = requests.get(
                    f"{self.base_url}/suno/fetch/{task_id}",
                    headers=self.headers,
                    timeout=30
                )
                fetch_response.raise_for_status()
                
                fetch_data = fetch_response.json()
                
                if fetch_data.get('code') == 'success' and fetch_data.get('data'):
                    data = fetch_data['data']
                    status = data.get('status', '')
                    
                    if status == 'complete':
                        logger.info(f"Music generation completed successfully!")
                        return data
                    elif status == 'error':
                        raise ValueError(f"Music generation failed: {data.get('error_message', 'Unknown error')}")
                    else:
                        logger.info(f"Status: {status} (attempt {attempt}/{max_attempts})")
                else:
                    logger.warning(f"Unexpected fetch response: {fetch_data}")
            
            raise TimeoutError("Music generation timed out after 5 minutes")
            
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
        # New CometAPI structure: result_data contains clips array
        audio_url = None
        
        # Try to find audio_url in the response
        if isinstance(result_data, dict):
            # Check for clips array (most common structure)
            if 'clips' in result_data and len(result_data['clips']) > 0:
                audio_url = result_data['clips'][0].get('audio_url')
            # Check for direct audio_url
            elif 'audio_url' in result_data:
                audio_url = result_data['audio_url']
            # Check for data array (older structure)
            elif 'data' in result_data and len(result_data['data']) > 0:
                audio_url = result_data['data'][0].get('audio_url')
        
        if not audio_url:
            logger.error(f"Could not find audio_url in response: {result_data}")
            raise ValueError("No audio URL in response data")
        
        logger.info(f"Found audio URL: {audio_url}")
        
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
