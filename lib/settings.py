import json

SETTINGS_FILE = "settings.json"

class Settings:
    """Stores the settings for the application."""
    def __init__(self):
        self.theme = "default"
    
    def save(self):
        """Saves the settings to the settings file."""
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.__dict__, f)
    
    @classmethod
    def load(cls):
        """Loads the settings from the settings file."""
        settings = cls()
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                settings.__dict__.update(data)
        except FileNotFoundError:
            pass
        return settings

    def restore(self):
        """Restores the settings from the settings file."""
        loaded_settings = self.load()
        self.__dict__.update(loaded_settings.__dict__)
    
    def edit_theme(self, new_theme: str):
        """Edits the theme setting."""
        self.theme = new_theme
    
    def needs_saving(self):
        """Indicates whether the settings are saved or not."""
        loaded_settings = self.load()
        return self.__dict__ != loaded_settings.__dict__
            