import pytest
from app.services.bkt import BKTParameters, update

P=BKTParameters(initial=.2,transition=.1,guess=.2,slip=.1)
def test_correct_observation_increases_mastery(): assert update(.2,True,P)==pytest.approx(.5764705882)
def test_incorrect_observation_applies_learning_transition(): assert update(.2,False,P)==pytest.approx(.127272727)
def test_probability_is_validated():
    with pytest.raises(ValueError): update(1.2,True,P)
