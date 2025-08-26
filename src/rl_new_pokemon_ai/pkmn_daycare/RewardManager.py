from dataclasses import dataclass 

from .Observation import Observation


@dataclass
class RewardCoeff:
    hp_loss: float
    status_change: float
    ko_pkmn: float
    # . . . add coeff how you feel it


class RewardManager:
    def __init__(self, coeffs: RewardCoeff):
        self.coeffs = coeffs
        self.episode_obs: npt.NDArray[Observation] = np.array([])

    def compute_reward(self, o: Observation) -> float:
        # positive reward for positive action : hp gain / positiv status / enemy damage / battle won / friend pkmn ko
        # negative reward for negative action : trying illegal move / negativ status effect / damage taken / battle lost / enemy pkmn ko
        return 0.0
