"""
OpenAI API Integration for Metadata and Thumbnail Generation
"""
import os
import logging
from typing import Dict, List
from retry import retry
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OpenAIGenerator:
    """Handle OpenAI API for text and image generation"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    @retry(tries=3, delay=5, backoff=2)
    def generate_video_metadata(self, music_prompt: str) -> Dict[str, any]:
        """
        Generate YouTube video metadata using GPT
        
        Args:
            music_prompt: The prompt used to generate the music
        
        Returns:
            Dictionary with title, description, tags, and thumbnail_prompt
        """
        logger.info("Generating video metadata with OpenAI...")
        
        system_prompt = """You are an expert YouTube content strategist specializing in lo-fi music channels.
Generate highly engaging, SEO-optimized metadata for lo-fi study music videos."""
        
        user_prompt = f"""Based on this lo-fi music description: "{music_prompt}"

Generate the following in JSON format:
1. A catchy YouTube title (under 70 characters, include keywords like "lofi", "study", "chill", "beats")
2. An SEO-optimized description (200-300 words, include relevant hashtags at the end)
3. 10-20 relevant tags (single words or short phrases)
4. A detailed thumbnail image prompt (describe an aesthetic lo-fi scene, specify "anime style", "16:9 ratio", "YouTube thumbnail")

Return ONLY valid JSON with these exact keys: title, description, tags, thumbnail_prompt"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON from response
            import json
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content.split("```json")[1]
            if content.startswith("```"):
                content = content.split("```")[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            
            content = content.strip()
            metadata = json.loads(content)
            
            logger.info(f"Generated title: {metadata.get('title')}")
            logger.info(f"Generated {len(metadata.get('tags', []))} tags")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            raise
    
    @retry(tries=3, delay=5, backoff=2)
    def generate_thumbnail(self, prompt: str, output_path: str) -> str:
        """
        Generate thumbnail image using DALL-E
        
        Args:
            prompt: Description of the image to generate
            output_path: Where to save the thumbnail
        
        Returns:
            Path to saved thumbnail
        """
        logger.info("Generating thumbnail with DALL-E...")
        logger.info(f"Thumbnail prompt: {prompt}")
        
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",  # Closest to 16:9, will be resized
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download the image
            import requests
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()
            
            # Save raw image
            temp_path = output_path.replace('.png', '_temp.png')
            with open(temp_path, 'wb') as f:
                f.write(img_response.content)
            
            # Resize to exact YouTube thumbnail specs (1280x720)
            self._resize_thumbnail(temp_path, output_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            logger.info(f"Thumbnail saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            raise
    
    def _resize_thumbnail(self, input_path: str, output_path: str):
        """
        Resize image to YouTube thumbnail specifications (1280x720)
        
        Args:
            input_path: Path to source image
            output_path: Path to save resized image
        """
        from PIL import Image
        
        with Image.open(input_path) as img:
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Resize to 1280x720 (16:9 aspect ratio)
            img_resized = img.resize((1280, 720), Image.Resampling.LANCZOS)
            img_resized.save(output_path, 'PNG', quality=95)
    
    def generate_complete_assets(self, music_prompt: str, thumbnail_path: str) -> Dict:
        """
        Generate all metadata and thumbnail in one call
        
        Args:
            music_prompt: The music generation prompt
            thumbnail_path: Where to save thumbnail
        
        Returns:
            Complete metadata dictionary including paths
        """
        # Generate text metadata
        metadata = self.generate_video_metadata(music_prompt)
        
        # Generate thumbnail using the AI-created prompt
        thumbnail_prompt = metadata.get('thumbnail_prompt', '')
        
        # Enhance thumbnail prompt with technical specs
        enhanced_prompt = f"{thumbnail_prompt}. High quality, vibrant colors, professional YouTube thumbnail style, 16:9 aspect ratio"
        
        self.generate_thumbnail(enhanced_prompt, thumbnail_path)
        
        # Add thumbnail path to metadata
        metadata['thumbnail_path'] = thumbnail_path
        
        return metadata

