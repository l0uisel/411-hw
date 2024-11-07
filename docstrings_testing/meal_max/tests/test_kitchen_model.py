from contextlib import contextmanager
import re
import sqlite3

import pytest

from kitchen_collection.models.ingredient_model import (
    Ingredient,
    add_ingredient
    delete_ingredient
    get_ingredient_by_id,
    get_all_ingredients,
    get_random_recipe
    update_quantity
)

######################################################
#
#    Fixtures
#
######################################################

# Took inspiration from test_song_model
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

    # Call the function to create a new song
    add_ingredient(type="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=800, Unit="grams")

    expected_query = normalize_whitespace("""
        INSERT INTO ingredients (type, name, expires, quantity, unit)
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
        add_ingredient(type="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=800, Unit="grams")

def test_add_ingredient_invalid_quantity():
    """Test error when trying to add an ingredient with an invalid quantity (e.g., negative quantity)"""

    # Attempt to add an ingredient with a negative quantity
    with pytest.raises(ValueError, match="Invalid ingredient quantity: -800 \(must be a positive integer\)."):
        add_ingredient(type="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=-800, Unit="grams")

    # Attempt to add an ingredient with a non-integer quantity
    with pytest.raises(ValueError, match="Invalid ingredient quantity: -800 \(must be a positive integer\)."):
        add_ingredient(type="Vegetable", name="Cabbage", expires="11/11/2024", Quantity=-800, Unit="grams")

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
    with pytest.raises(ValueError, match="Ingrdient with ID 888 not found"):
        delete_ingredient(888)

def test_delete_ingredient_already_deleted(mock_cursor):
    """Test error when trying to delete an ingredient already deleted."""

    # Simulate that the song exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a song that's already been deleted
    with pytest.raises(ValueError, match="Ingredient with ID 888 has already been deleted"):
        delete_ingredient(888)
