import os
import ujson as json


class FavoritesManager:
    def __init__(self, fav_path):
        self.fav_path = fav_path
        self.favorites = self.load_favorites()

    def load_favorites(self):
        if os.path.exists(self.fav_path):
            try:
                with open(self.fav_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_favorites(self):
        try:
            with open(self.fav_path, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Handled exception: {e}")

    def is_favorite(self, reciter_id):
        return str(reciter_id) in [str(x) for x in self.favorites]

    def add_favorite(self, reciter_id):
        rec_str = str(reciter_id)
        if rec_str not in [str(x) for x in self.favorites]:
            self.favorites.append(rec_str)
            self.save_favorites()

    def remove_favorite(self, reciter_id):
        rec_str = str(reciter_id)
        self.favorites = [x for x in self.favorites if str(x) != rec_str]
        self.save_favorites()

    def toggle_favorite(self, reciter_id):
        if self.is_favorite(reciter_id):
            self.remove_favorite(reciter_id)
            return False
        else:
            self.add_favorite(reciter_id)
            return True
