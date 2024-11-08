from contextlib import contextmanager
import re
import sqlite3

import pytest

from kitchen_collection.models.ingredient_model import (
    Ingredient,
    add_ingredient,
    delete_ingredient,
    get_ingredient_by_id,
    get_all_ingredients,
    get_random_ingredient,
    update_quantity
)

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

    mocker.patch("kitchen_collection.models.ingredient_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_add_ingredient(mock_cursor):
    """Test adding ingredients to storage."""

    # Call the function to create a new ingredient
    add_ingredient(ingredtype="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=800, Unit="grams")

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
    expected_arguments = ("Vegetable", "Cabbage", "11/11/2024", 800, "grams")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_add_ingredient_duplicate(mock_cursor):
    """Test adding a duplicate ingredient (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: ingredients.name")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Ingredient 'Cabbage' already exists."):
        add_ingredient(ingredtype="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=800, Unit="grams")

def test_add_ingredient_invalid_quantity():
    """Test error when trying to add an ingredient with an invalid quantity (e.g., negative quantity)"""

    # Attempt to add an ingredient with a negative quantity
    with pytest.raises(ValueError, match="Invalid ingredient quantity: -800 \(must be a positive integer\)."):
        add_ingredient(ingredtype="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=-800, Unit="grams")

    # Attempt to add an ingredient with a non-integer quantity
    with pytest.raises(ValueError, match="Invalid ingredient quantity: -800 \(must be a positive integer\)."):
        add_ingredient(ingredtype="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=-800, Unit="grams")

def test_delete_ingredient(mock_cursor):
    """Test deleting an ingredient from the kitchen by ingredient ID."""

    # Simulate that the ingredient exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_ingredient function
    delete_ingredient(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM ingredients WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE ingredients SET deleted = TRUE WHERE id = ?")

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

def test_delete_ingredient_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent ingredient."""

    # Simulate that no ingredient exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent ingredient
    with pytest.raises(ValueError, match="Ingredient with ID 888 not found"):
        delete_ingredient(888)

def test_delete_ingredient_already_deleted(mock_cursor):
    """Test error when trying to delete an ingredient already deleted."""

    # Simulate that the ingredient exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a ingredient that's already been deleted
    with pytest.raises(ValueError, match="Ingredient with ID 888 has already been deleted"):
        delete_ingredient(888)

######################################################
#
#    Get Ingredient
#
######################################################

def test_get_ingredient_by_id(mock_cursor):
    """Test retrieving an ingredient by ID."""
    # Simulate that the ingredient exists (id = 1)
    mock_cursor.fetchone.return_value = (1, ingredtype="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=800, Unit="grams")

    # Call the function and check the result
    result = get_ingredient_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Ingredient(1, ingredtype="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=800, Unit="grams")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, ingredtype, name, expires, quantity, unit FROM ingredients WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_ingredient_by_id_bad_id(mock_cursor):
    """Test retrieving an ingredient using non-existent ID."""
    # Simulate that no ingredient exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the ingredient is not found
    with pytest.raises(ValueError, match="Ingredient with ID 888 not found"):
        get_ingredient_by_id(888)

def test_get_all_ingredients(mock_cursor):
    """Test getting all in-stock ingredients."""

    # Simulate that there are multiple ingredients in stock
    mock_cursor.fetchall.return_value = [
        (1, "Powder", "Flour", "11/11/2024", 10, "kg"),
        (2, "Dairy", "Milk", "11/11/2024", 20, "liters")
        (3, "Dairy", "Butter", "11/11/2024", 30, "sticks") 
    ]

    # Call the get_all_ingredients function
    ingredients = get_all_ingredients()

    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "ingredtype": "Powder", "name": "Flour", "expires": "11/11/2024", "quantity": 10,  "unit": "kg"},
        {"id": 2, "ingredtype": "Dairy", "name": "Milk", "expires": "11/11/2024", "quantity": 20,  "unit": "liters"},
        {"id": 1, "ingredtype": "Dairy", "name": "Butter", "expires": "11/11/2024", "quantity": 30,  "unit": "sticks"},
    ]

    assert ingredients == expected_result, f"Expected {expected_result}, but got {ingredients}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, ingredtype, name, expires, quantity, unit FROM ingredients WHERE quantity > 0")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_random_ingredient(mock_cursor, mocker):
    """Test retrieving a random ingredient from the catalog."""

    # Simulate that there are multiple ingredients in the database
    mock_cursor.fetchall.return_value = [
        (1, "Powder", "Flour", "11/11/2024", 10, "kg"),
        (2, "Dairy", "Milk", "11/11/2024", 20, "liters")
        (3, "Dairy", "Butter", "11/11/2024", 30, "sticks") 
    ]

    # Mock random number generation to return the 2nd ingredient
    mock_random = mocker.patch("kitchen_management.models.ingredient_model.get_random", return_value=2)

    # Call the get_random_ingredient method
    result = get_random_ingredient()

    # Expected result based on the mock random number and fetchall return value
    expected_result = {"id": 1, "ingredtype": "Dairy", "name": "Butter", "expires": "11/11/2024", "quantity": 30,  "unit": "sticks"},
    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure that the random number was called with the correct number of ingredients
    mock_random.assert_called_once_with(3)

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, ingredtype, name, expires, quantity, unit FROM ingredients")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

######################################################
#
#    Updating Stock
#
######################################################
        
def test_update_quantity(mock_cursor):
    """Test updating the ingredient quantity."""

    # Simulate that the ingredient exists (id = 1, name = "Flour")
    mock_cursor.fetchone.return_value = [True]

    # Call the update_ingredient_quantity function with a sample ingredient ID and quantity
    ingredient_id = 1
    new_quantity = 15
    update_quantity(ingredient_id, new_quantity)

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("UPDATE ingredients SET quantity = ? WHERE id = ?")

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (ingredient ID and new quantity)
    expected_arguments = (new_quantity, ingredient_id)
    assert actual_arguments == expected_arguments, f"Expected {expected_arguments}, got {actual_arguments}."

def test_update_quantity_for_unavailable_ingredient(mock_cursor):
    """Test error when trying to update a non-existing ingredient quantity."""

    # Simulate that the ingredient does not exist (id = 888)
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError to be raised when calling update_ingredient_quantity with a non-existent ingredient
    with pytest.raises(ValueError, match="Ingredient with ID 888 does not exist"):
        update_quantity(888, 15)

    # Ensure that no SQL query for updating quantity was executed
    mock_cursor.execute.assert_called_once_with("SELECT id FROM ingredients WHERE id = ?", (888))