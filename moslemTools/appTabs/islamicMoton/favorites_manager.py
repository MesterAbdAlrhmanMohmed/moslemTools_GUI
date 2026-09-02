import os
import ujson as json
from settings import app

class MotonFavoritesManager:
    def __init__(self):
        self.fav_file_path = os.path.join(os.getenv("appdata"), app.appName, "moton_favorites.json")
        self.favorites = []
        self.show_favorites_only = False
        self.load_favorites()

    def load_favorites(self):
        try:
            if os.path.exists(self.fav_file_path):
                with open(self.fav_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.favorites = data.get("favorites", [])
                        self.show_favorites_only = data.get("show_favorites_only", False)
                    else:
                        self.favorites = data
                        self.show_favorites_only = False
            else:
                self.favorites = []
                self.show_favorites_only = False
        except Exception:
            self.favorites = []
            self.show_favorites_only = False

    def save_favorites(self):
        try:
            os.makedirs(os.path.dirname(self.fav_file_path), exist_ok=True)
            with open(self.fav_file_path, "w", encoding="utf-8") as f:
                json.dump({"favorites": self.favorites, "show_favorites_only": self.show_favorites_only}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def is_favorite(self, matn_name):
        return matn_name in self.favorites

    def add_favorite(self, matn_name):
        if matn_name not in self.favorites:
            self.favorites.append(matn_name)
            self.save_favorites()
            return True
        return False

    def remove_favorite(self, matn_name):
        if matn_name in self.favorites:
            self.favorites.remove(matn_name)
            self.save_favorites()
            return True
        return False

    def toggle_favorite(self, matn_name):
        if self.is_favorite(matn_name):
            self.remove_favorite(matn_name)
            return False
        else:
            self.add_favorite(matn_name)
            return True
