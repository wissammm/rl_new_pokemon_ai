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
        self.episode_obs : npt.NDArray[Observation] = np.array([])

    def compute_reward(self, o : Observation) -> float:
        return 0.0
        
    def compute_positive_reward(self, o : Observation) -> float:
        return 0.0
        
