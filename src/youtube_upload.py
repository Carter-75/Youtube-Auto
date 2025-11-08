"""
YouTube Data API v3 Integration for Video Upload
"""
import os
import logging
import pickle
from typing import Dict, Optional
from retry import retry
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubeUploader:
    """Handle YouTube video upload and metadata"""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with YouTube API using OAuth2"""
        creds = None
        token_path = 'token.pickle'
        
        # Try to load existing credentials
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid creds, use refresh token or run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing access token...")
                creds.refresh(Request())
            elif self.refresh_token:
                # Create credentials from refresh token
                logger.info("Creating credentials from refresh token...")
                creds = Credentials(
                    None,
                    refresh_token=self.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                creds.refresh(Request())
            else:
                logger.info("Starting OAuth2 flow...")
                # Create client config
                client_config = {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.youtube = build('youtube', 'v3', credentials=creds)
        logger.info("Successfully authenticated with YouTube API")
    
    @retry(tries=3, delay=10, backoff=2)
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        category_id: str = "10",
        privacy_status: str = "private"
    ) -> str:
        """
        Upload video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category (10 = Music)
            privacy_status: "private", "public", or "unlisted"
        
        Returns:
            Video ID of uploaded video
        """
        logger.info(f"Uploading video: {title}")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        try:
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"[UPLOAD] Progress: {progress}%")
            
            video_id = response['id']
            logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            logger.info(f"Video URL: https://www.youtube.com/watch?v={video_id}")
            
            return video_id
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise
    
    @retry(tries=3, delay=5, backoff=2)
    def set_thumbnail(self, video_id: str, thumbnail_path: str):
        """
        Upload custom thumbnail for video
        
        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image
        """
        logger.info(f"Uploading thumbnail for video {video_id}")
        
        try:
            media = MediaFileUpload(thumbnail_path, mimetype='image/png')
            
            request = self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            )
            
            response = request.execute()
            logger.info("Thumbnail uploaded successfully!")
            
        except HttpError as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            raise
    
    def upload_complete_video(
        self,
        video_path: str,
        thumbnail_path: str,
        metadata: Dict,
        privacy_status: str = "private"
    ) -> Dict:
        """
        Complete upload workflow: video + thumbnail + metadata
        
        Args:
            video_path: Path to video file
            thumbnail_path: Path to thumbnail image
            metadata: Dictionary with title, description, tags
            privacy_status: Video privacy setting
        
        Returns:
            Dictionary with video_id and video_url
        """
        # Upload video
        video_id = self.upload_video(
            video_path=video_path,
            title=metadata['title'],
            description=metadata['description'],
            tags=metadata['tags'],
            category_id="10",  # Music category
            privacy_status=privacy_status
        )
        
        # Upload thumbnail
        self.set_thumbnail(video_id, thumbnail_path)
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        return {
            'video_id': video_id,
            'video_url': video_url
        }

