#!/bin/bash

# Base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;  # Enable JSON output if flag is passed
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

###############################################
#
# Health checks
#
###############################################

check_health() {
  echo "Checking health status..."
  # Perform a health check by calling the /health endpoint
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

check_db() {
  echo "Checking database connection..."
  # Perform a database check by calling the /db-check endpoint
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

###############################################
#
# Meal Management
#
###############################################

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Creating a new meal: $meal ($cuisine, $price, $difficulty)..."
  # Build the JSON payload for meal creation
  meal_data="{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price, \"difficulty\": \"$difficulty\"}"
  
  # Send POST request to create the meal
  response=$(curl -s -X POST -H "Content-Type: application/json" -d "$meal_data" "$BASE_URL/create-meal")
  
  # Check if the creation was successful
   if echo "$response" | grep -q '"status": "success"'; then

    echo "Meal created successfully."

    if [ "$ECHO_JSON" = true ]; then

      echo "Create Meal JSON:"

      echo "$response" | jq .
    fi
  else
    echo "Failed to create meal."
    exit 1
  fi
}

clear_meals() {
  echo "Clearing meals..."
  # Send DELETE request to clear all meals
  response=$(curl -s -X DELETE "$BASE_URL/clear-meals")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meals cleared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Clear Meals JSON:"
    fi
  else
    echo "Failed to clear meals."
    exit 1
  fi
}

delete_meal() {
  local meal_id=$1
  echo "Deleting meal with ID: $meal_id..."
  # Send DELETE request to delete the specific meal
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Delete Meal JSON:"
    fi
  else
    echo "Failed to delete meal."
    exit 1
  fi
}

get_meal_by_id() {
  local meal_id=$1
  echo "Getting meal by ID: $meal_id..."
  # Request to retrieve the specific meal by ID
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Get Meal by ID JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID."
    exit 1
  fi
}

get_meal_by_name() {
  local meal_name=$1
  echo "Getting meal by name: $meal_name..."
  # Request to retrieve the specific meal by name
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Get Meal by Name JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name."
    exit 1
  fi
}

###############################################
#
# Battle
#
###############################################

battle() {
  echo "Starting a battle..."
  # Send GET request to initiate a battle
  response=$(curl -s -X GET "$BASE_URL/battle")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle completed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle JSON:"
    fi
  else
    echo "Battle failed."
    exit 1
  fi
}

###############################################
#
# Combatants
#
###############################################

prep_combatant() {
  local meal_name="$1"
  echo "Preparing combatant: $meal_name..."
  
  # Ensure meal_name is properly escaped for JSON
  prep_data="{\"meal\": \"$meal_name\"}"
  
  # POST request to prepare the combatant
  response=$(curl -s -X POST -H "Content-Type: application/json" -d "$prep_data" "$BASE_URL/prep-combatant")

  # Check if the response indicates success
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant prepared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Prep Combatant JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to prepare combatant."
    echo "Response: $response"  # Output the full response for debugging
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing combatants..."
  # Send POST request to clear all combatants
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Clear Combatants JSON:"
    fi
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

get_combatants() {
  echo "Getting combatants..."
  # Send GET request to retrieve all combatants
  response=$(curl -s -X GET "$BASE_URL/get-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Get Combatants JSON:"
    fi
  else
    echo "Failed to get combatants."
    exit 1
  fi
}

# ###############################################
#
# Leaderboard
#
# ###############################################

get_leaderboard() {
  echo "Getting leaderboard..."
    # Request to retrieve the leaderboard
  response=$(curl -s -X GET "$BASE_URL/leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get leaderboard."
    exit 1
  fi
}

# ###############################################
#
# Further Tests
#
# ###############################################

# Health checks
check_health
check_db

# Clear the meals and create new ones
clear_meals
create_meal "Taco" "Mexican" 5.00 "LOW"
create_meal "Spaghetti" "Italian" 15.00 "MED"
create_meal "Sushi" "Japanese" 18.50 "HIGH"

# Delete a meal by ID and get meal details
delete_meal 1
get_meal_by_id 2
get_meal_by_name "Spaghetti"

# Prepare combatants and run battles
prep_combatant "Spaghetti"
prep_combatant "Sushi"
get_combatants
battle
clear_combatants

prep_combatant "Spaghetti"
prep_combatant "Taco"
get_combatants
battle
clear_combatants

# Get leaderboard and show results
get_leaderboard

echo "All tests passed successfully!"