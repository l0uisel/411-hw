from contextlib import contextmanager
import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

######################################################
#
#    Fixtures
#
######################################################

@pytest.fixture
def battle_model():
    """Returns a fresh BattleModel instance for each test."""
    return BattleModel()

@pytest.fixture
def sample_meals():
    """Returns sample meal instances for testing."""
    return [
        Meal(id=1, meal="Spaghetti", cuisine="Italian", price=15.00, difficulty="MED"),
        Meal(id=2, meal="Sushi", cuisine="Japanese", price=20.00, difficulty="HIGH")
    ]

@pytest.fixture
def mock_random(mocker):
    """Mock the random number generator."""
    return mocker.patch("meal_max.utils.random_utils.get_random", return_value=0.5)

@pytest.fixture
def mock_update_stats(mocker):
    """Mock the update_meal_stats function."""
    return mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

######################################################
#
#    Battle Model Tests
#
######################################################

def test_battle_model_init(battle_model):
    """Test BattleModel initialization."""
    assert isinstance(battle_model, BattleModel)
    assert battle_model.combatants == []

######################################################
#
#    Combatant Management Tests
#
######################################################

def test_prep_combatant(battle_model, sample_meals):
    """Test adding a combatant to the battle."""
    battle_model.prep_combatant(sample_meals[0])
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0] == sample_meals[0]

def test_prep_combatant_full_list(battle_model, sample_meals):
    """Test error when adding combatant to full list."""
    battle_model.prep_combatant(sample_meals[0])
    battle_model.prep_combatant(sample_meals[1])
    
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meals[0])

def test_clear_combatants(battle_model, sample_meals):
    """Test clearing combatants from battle."""
    battle_model.prep_combatant(sample_meals[0])
    battle_model.prep_combatant(sample_meals[1])
    
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0

def test_get_combatants(battle_model, sample_meals):
    """Test retrieving current combatants."""
    battle_model.prep_combatant(sample_meals[0])
    battle_model.prep_combatant(sample_meals[1])
    
    combatants = battle_model.get_combatants()
    assert len(combatants) == 2
    assert combatants == sample_meals

######################################################
#
#    Battle Score Tests
#
######################################################

def test_get_battle_score(battle_model, sample_meals):
    """Test battle score calculation."""
    # For meal: "Spaghetti", cuisine: "Italian" (7 chars), price: 15.00, difficulty: "MED" (modifier: 2)
    # Expected score: 15.00 * 7 - 2 = 103
    score = battle_model.get_battle_score(sample_meals[0])
    assert score == 103.0

def test_get_battle_score_different_difficulties(battle_model):
    """Test battle score calculation with different difficulties."""
    meals = [
        Meal(id=1, meal="Test", cuisine="Test", price=10.00, difficulty="LOW"),  # 10 * 4 - 3 = 37
        Meal(id=2, meal="Test", cuisine="Test", price=10.00, difficulty="MED"),  # 10 * 4 - 2 = 38
        Meal(id=3, meal="Test", cuisine="Test", price=10.00, difficulty="HIGH")  # 10 * 4 - 1 = 39
    ]
    
    scores = [battle_model.get_battle_score(meal) for meal in meals]
    assert scores == [37.0, 38.0, 39.0]

######################################################
#
#    Battle Execution Tests
#
######################################################

def test_battle_insufficient_combatants(battle_model, sample_meals):
    """Test error when battling with insufficient combatants."""
    battle_model.prep_combatant(sample_meals[0])
    
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle_execution(battle_model, sample_meals, mock_random, mock_update_stats):
    """Test complete battle execution with controlled random outcome."""
    battle_model.prep_combatant(sample_meals[0])  # Spaghetti
    battle_model.prep_combatant(sample_meals[1])  # Sushi
    
    # With mock_random returning 0.5 and delta being |103 - 139| / 100 = 0.36
    # Sushi (combatant_2) should win as delta < random_number
    winner = battle_model.battle()
    
    assert winner == "Sushi"
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == "Sushi"
    
    # Verify stat updates were called correctly
    mock_update_stats.assert_any_call(2, 'win')  # Sushi won
    mock_update_stats.assert_any_call(1, 'loss')  # Spaghetti lost

def test_battle_different_random_outcome(battle_model, sample_meals, mock_update_stats, mocker):
    """Test battle with different random outcome."""
    # Mock random to return 0.2 (lower than delta of 0.36)
    mocker.patch("meal_max.utils.random_utils.get_random", return_value=0.2)
    
    battle_model.prep_combatant(sample_meals[0])  # Spaghetti
    battle_model.prep_combatant(sample_meals[1])  # Sushi
    
    # With random_number = 0.2 and delta = 0.36
    # Spaghetti (combatant_1) should win as delta > random_number
    winner = battle_model.battle()
    
    assert winner == "Spaghetti"
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == "Spaghetti"
    
    # Verify stat updates were called correctly
    mock_update_stats.assert_any_call(1, 'win')  # Spaghetti won
    mock_update_stats.assert_any_call(2, 'loss')  # Sushi lost