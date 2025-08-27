from typing import Any, Dict


class EpisodeManager:
    """
    Manages episode lifecycle and state tracking.
    """

    def __init__(self):
        self.episode_rewards = {"player": 0.0, "enemy": 0.0}
        self.episode_steps = 0
        self.max_episode_steps = 1000  # Configurable

    def reset_episode(self):
        """Reset episode state"""
        self.episode_rewards = {"player": 0.0, "enemy": 0.0}
        self.episode_steps = 0

    def update_episode(self, rewards: Dict[str, float] = None):
        """Update episode state"""
        self.episode_steps += 1

        if rewards:
            for agent, reward in rewards.items():
                self.episode_rewards[agent] += reward

    def is_episode_done(self, battle_done: bool) -> bool:
        """Check if episode should end"""
        return battle_done or self.episode_steps >= self.max_episode_steps

    def get_episode_info(self) -> Dict[str, Any]:
        """Get episode information"""
        return {
            "episode_rewards": self.episode_rewards.copy(),
            "episode_steps": self.episode_steps,
            "max_steps_reached": self.episode_steps >= self.max_episode_steps,
        }
