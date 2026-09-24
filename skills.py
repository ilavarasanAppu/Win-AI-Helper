import os
import json

DEFAULT_SKILLS = [
    {
        "name": "🎯 Direct Answer Only",
        "prompt": "IMPORTANT: Return ONLY the direct answer. Do NOT include any explanations, introductions, conclusions, meta-commentary, or suggestions."
    },
    {
        "name": "📄 JSON Format Only",
        "prompt": "IMPORTANT: Return ONLY valid JSON format matching the request. Do NOT wrap in markdown explanation or conversational text."
    },
    {
        "name": "🔤 Tanglish",
        "prompt": "IMPORTANT: Respond strictly in Tanglish (Tamil language written using English alphabet). Keep the answer direct and natural."
    },
    {
        "name": "💻 Code Only",
        "prompt": "IMPORTANT: Return ONLY executable code inside code block. Do NOT include any conversational introduction or explanation."
    }
]


class SkillManager:
    """Manages custom prompt skills loaded from skills.json."""

    def __init__(self, filepath: str = None):
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), "skills.json")
        self.filepath = filepath
        self.active_skill_name = "🎯 Direct Answer Only"
        self.skills = []
        self.load_skills()

    def load_skills(self):
        """Load skills from JSON file, creating defaults if missing."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_skill_name = data.get("active_skill", "🎯 Direct Answer Only")
                    self.skills = data.get("skills", DEFAULT_SKILLS)
                    return
            except Exception as e:
                print(f"Error loading skills.json: {e}")
        
        # Default skills if file doesn't exist or failed to parse
        self.skills = list(DEFAULT_SKILLS)
        self.save_skills()

    def save_skills(self):
        """Save current skills to skills.json."""
        try:
            data = {
                "active_skill": self.active_skill_name,
                "skills": self.skills
            }
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving skills.json: {e}")

    def get_skill_names(self) -> list[str]:
        return [s["name"] for s in self.skills]

    def get_active_skill_prompt(self) -> str:
        if not self.active_skill_name or self.active_skill_name == "None (Default)":
            return ""
        for s in self.skills:
            if s["name"] == self.active_skill_name:
                return s.get("prompt", "")
        return ""

    def add_skill(self, name: str, prompt: str):
        """Add or update a custom skill."""
        for s in self.skills:
            if s["name"] == name:
                s["prompt"] = prompt
                self.save_skills()
                return
        self.skills.append({"name": name, "prompt": prompt})
        self.save_skills()

    def set_active_skill(self, name: str):
        self.active_skill_name = name
        self.save_skills()
