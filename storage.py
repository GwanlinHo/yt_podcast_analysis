import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, Optional, List
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "database.json")
ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis")

@dataclass
class Video:
    id: str
    title: str
    url: str
    date: str  # YYYYMMDD
    channel: str
    status: str = "pending"  # pending, analyzed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

class Storage:
    def __init__(self):
        self._ensure_dirs()
        self.videos: Dict[str, Video] = {}
        self.load_database()

    def _ensure_dirs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(ANALYSIS_DIR, exist_ok=True)

    def load_database(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Load videos
                    for v_data in data.get("videos", {}).values():
                        # Handle potential missing fields if schema changes
                        # Using **v_data safely requires v_data to match Video fields exactly
                        # or we construct it explicitly.
                        # For now, assuming straightforward mapping.
                        self.videos[v_data['id']] = Video(**v_data)
            except Exception as e:
                print(f"Error loading database: {e}")
                self.videos = {}
        else:
            self.videos = {}

    def save_database(self):
        data = {
            "last_updated": datetime.now().isoformat(),
            "videos": {v_id: asdict(video) for v_id, video in self.videos.items()}
        }
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")

    def upsert_video(self, video: Video) -> bool:
        """
        Add or update video.
        Returns True if a new video was added.
        """
        if video.id not in self.videos:
            self.videos[video.id] = video
            return True
        else:
            # If exists, we might want to update metadata but preserve status
            existing = self.videos[video.id]
            # Update title/url if changed (unlikely for ID match but possible)
            existing.title = video.title
            existing.url = video.url
            # do not overwrite status or created_at
            return False

    def get_pending_videos(self) -> List[Video]:
        """Returns list of videos with status 'pending'."""
        return [v for v in self.videos.values() if v.status == "pending"]

    def get_videos_by_date_range(self, start_date: str, end_date: str) -> List[Video]:
        """
        Returns list of videos within date range (inclusive).
        date format: YYYYMMDD
        """
        result = []
        for v in self.videos.values():
            if start_date <= v.date <= end_date:
                result.append(v)
        # Sort by date descending
        return sorted(result, key=lambda x: x.date, reverse=True)

    def save_analysis(self, video_id: str, content: dict):
        """
        Saves analysis result to JSON file and updates video status to 'analyzed'.
        """
        file_path = os.path.join(ANALYSIS_DIR, f"{video_id}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            # Update status in DB
            if video_id in self.videos:
                self.videos[video_id].status = "analyzed"
                self.save_database()
            else:
                print(f"Warning: Saving analysis for unknown video_id {video_id}")
        except Exception as e:
            print(f"Error saving analysis: {e}")

    def get_analysis(self, video_id: str) -> Optional[dict]:
        """Reads analysis result from JSON file."""
        file_path = os.path.join(ANALYSIS_DIR, f"{video_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading analysis: {e}")
                return None
        return None
