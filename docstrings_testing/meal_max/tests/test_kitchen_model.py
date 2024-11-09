from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals, 
    delete_meal, 
    get_leaderboard,
    get_meal_by_id, 
    get_meal_by_name,
    update_meal_stats
    )

######################################################
#
#    Fixtures
#
######################################################

# Inspiration from test_song_model

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test adding new meal to database."""

    # Call the function to create a new ingredient
    create_meal(meal="Spaghetti", cuisine="Italian", price=15.00, difficulty="LOW")

    expected_query = normalize_whitespace("""
        INSERT INTO ingredients (ingredtype, name, expires, quantity, unit)
        VALUES (?, ?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Spaghetti", "Italian", 15.00, "LOW")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test adding a duplicate meal (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: ingredients.name")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Spaghetti', cuisine 'Italian', price '15.00' and difficulty 'LOW' already exists."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=15.00, difficulty="LOW")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative quantity)"""

    # Attempt to add a meal with a negative price
    with pytest.raises(ValueError, match="Invalid meal price: -15.00 \(must be a positive number\)."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=-15.00, difficulty="LOW")

    # Attempt to add a meal with a non-numeric price
    with pytest.raises(ValueError, match="Invalid ingredient quantity: -800 \(must be a positive integer\)."):
        create_meal(meal="Spaghetti", cuisine="Italian", price="ten", difficulty="LOW")

def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the database by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_meal function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_create_meal_invalid_difficulty():
    """Test erorr when trying to create a meal with an invalid difficulty."""

    with pytest.raises(
        ValueError,
        match="Invalid difficulty level: 'EASY'. Must be 'LOW', 'MED', or 'HIGH'.",
    ):
        create_meal(meal="Sushi", cuisine="Japanese", price=18.50, difficulty="HIGH")

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has alreadyt been deleted"):
        delete_meal(999)

def test_clear_meals(mock_cursor, mocker):
    """Test clearing all the meals (removes all meals)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_song_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()

######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    """Test retrieving a meal by its ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Spaghetti", "Italian", 15.00, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(id=1, meal="Spaghetti", cuisine="Italian", price=15.00, difficulty="LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_meal_by_id_bad_id(mock_cursor):
    """Test error when trying to retrieve a non-existent meal by ID."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to retrieve a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_name(mock_cursor):
    """Test retrieving a meal by its name."""

    # Simulate that the meal exists (name = "Spaghetti")
    mock_cursor.fetchone.return_value = (1, "Spaghetti", "Italian", 15.00, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_name("Spaghetti")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(id=1, meal="Spaghetti", cuisine="Italian", price=15.00, difficulty="MED")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Spaghetti",)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_name_bad_name(mock_cursor):
    """Test error when trying to retrieve a meal with a non-existent name."""

    # Simulate that no meal exists with the given name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with name 'NonExistentMeal' not found"):
        get_meal_by_name("NonExistentMeal")

def test_get_meal_by_name_deleted(mock_cursor):
    """Test error when trying to retrieve a meal that's marked as deleted."""

    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = (1, "Spaghetti", "Italian", 15.00, "MED", True)

    # Expect a ValueError when attempting to retrieve a deleted meal
    with pytest.raises(ValueError, match="Meal with name 'Spaghetti' has been deleted"):
        get_meal_by_name("Spaghetti")

######################################################
#
#    Leaderboard
#
######################################################
def test_get_leaderboard_sorted_by_wins(mock_cursor):
    """Test retrieving the leaderboard sorted by total wins."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Spaghetti", "Italian", 15.00, "MED", 40, 30, 0.75),
        (2, "Taco", "Mexican", 5.00, "LOW", 30, 18, 0.6),
        (3, "Sushi", "Japanese", 18.50, "HIGH", 10, 8, 0.8)
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard(sort_by="wins")

    # Expected result based on the simulated fetchall return value
    expected_result = [
        {'id': 2, 'meal': 'Taco', 'cuisine': 'Mexican', 'price': 5.00, 'difficulty': 'LOW', 'battles': 40, 'wins': 30, 'win_pct': 75.0},
        {'id': 1, 'meal': 'Spaghetti', 'cuisine': 'Italian', 'price': 15.00, 'difficulty': 'MED', 'battles': 30, 'wins': 18, 'win_pct': 60.0},
        {'id': 3, 'meal': 'Sushi', 'cuisine': 'Japanese', 'price': 18.50, 'difficulty': 'HIGH', 'battles': 10, 'wins': 8, 'win_pct': 80.0}
    ]

    # Ensure the result matches the expected output
    assert leaderboard == expected_result, f"Expected {expected_result}, got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_sorted_by_win_pct(mock_cursor):
    """Test retrieving the leaderboard sorted by win percentage."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Spaghetti", "Italian", 15.00, "MED", 40, 30, 0.75),
        (2, "Taco", "Mexican", 5.00, "LOW", 30, 18, 0.6),
        (3, "Sushi", "Japanese", 18.50, "HIGH", 10, 8, 0.8)
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard(sort_by="win_pct")

    # Expected result based on the simulated fetchall return value
    expected_result = [
        {'id': 2, 'meal': 'Taco', 'cuisine': 'Mexican', 'price': 5.00, 'difficulty': 'LOW', 'battles': 40, 'wins': 30, 'win_pct': 75.0},
        {'id': 1, 'meal': 'Spaghetti', 'cuisine': 'Italian', 'price': 15.00, 'difficulty': 'MED', 'battles': 30, 'wins': 18, 'win_pct': 60.0},
        {'id': 3, 'meal': 'Sushi', 'cuisine': 'Japanese', 'price': 18.50, 'difficulty': 'HIGH', 'battles': 10, 'wins': 8, 'win_pct': 80.0}
   ]

    # Ensure the result matches the expected output
    assert leaderboard == expected_result, f"Expected {expected_result}, got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_invalid_sort_by(mock_cursor):
    """Test error when an invalid sort_by parameter is provided."""

    # Expect a ValueError when an invalid sort_by parameter is provided
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        get_leaderboard(sort_by="invalid")

    # Ensure that no SQL query was executed
    mock_cursor.execute.assert_not_called()

######################################################
#
#    Updating Stats
#
######################################################

def test_update_meal_stats_win(mock_cursor):
    """Test updating meal stats with a win result."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = (False,)

    # Call the update_meal_stats function with a win result
    meal_id = 1
    update_meal_stats(meal_id, "win")

    # Normalize the expected SQL query
    expected_select_query = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")

    # Ensure the SELECT SQL query was executed correctly
    actual_select_query = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    assert actual_select_query == expected_select_query, "The SELECT query did not match the expected structure."

    # Ensure the UPDATE SQL query was executed correctly
    actual_update_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    assert actual_update_query == expected_update_query, "The UPDATE query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_loss(mock_cursor):
    """Test updating meal stats with a loss result."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a loss result
    meal_id = 1
    update_meal_stats(meal_id, "loss")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1 WHERE id = ?")

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test error when updating meal stats with an invalid result."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Expect a ValueError when an invalid result is provided
    with pytest.raises(ValueError, match="Invalid result: invalid. Expected 'win' or 'loss'."):
        update_meal_stats(1, "invalid")

    # Ensure that no SQL query for updating stats was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when updating stats for a deleted meal."""

    # Simulate that the meal exists but is marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")

    # Ensure that no SQL query for updating stats was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

def test_update_meal_stats_nonexistent_meal(mock_cursor):
    """Test error when updating stats for a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to update a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, "win")

    # Ensure that no SQL query for updating stats was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (999,))