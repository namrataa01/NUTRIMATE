import os
import psutil
import time
import subprocess
import fnmatch
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import ImageFilter, Image
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
 
# Load datasets once at the top
try:
    # Change this path to wherever your CSV is located
    data = pd.read_csv('food_with_cuisine_extended.csv')
    Breakfastdata = data['Breakfast']
    BreakfastdataNumpy = Breakfastdata.to_numpy()

    Lunchdata = data['Lunch']
    LunchdataNumpy = Lunchdata.to_numpy()

    Dinnerdata = data['Dinner']
    DinnerdataNumpy = Dinnerdata.to_numpy()

    Food_itemsdata = data['Food_items'].tolist()
    
    # Check if Cuisine column exists
    if 'Cuisine' in data.columns:
        # Get unique cuisines
        unique_cuisines = data['Cuisine'].unique()
        print(f"Available cuisines: {unique_cuisines}")
    else:
        # If Cuisine column doesn't exist, create one with default values
        print("No Cuisine column found, creating default cuisines")
        # Assign random cuisines for demonstration purposes
        cuisines = ['Italian', 'Indian', 'Chinese', 'Mediterranean', 'Mexican', 'American']
        data['Cuisine'] = np.random.choice(cuisines, size=len(data))
        unique_cuisines = cuisines
    
    print("Data loaded successfully!")
except Exception as e:
    print(f"Error loading data: {e}")
    # Sample data in case file is not found
    data = pd.DataFrame({
        'Food_items': ["Oatmeal with fruits", "Eggs and toast", "Grilled chicken salad", 
                       "Vegetable stir-fry", "Salmon with brown rice", "Greek yogurt with berries"],
        'Breakfast': [1, 1, 0, 0, 0, 1],
        'Lunch': [0, 0, 1, 1, 0, 0],
        'Dinner': [0, 0, 0, 1, 1, 0],
        'Veg': [1, 0, 0, 1, 0, 1],
        'Cuisine': ['American', 'American', 'Mediterranean', 'Chinese', 'Japanese', 'Greek']
    })
    Breakfastdata = data['Breakfast']
    BreakfastdataNumpy = Breakfastdata.to_numpy()
    Lunchdata = data['Lunch']
    LunchdataNumpy = Lunchdata.to_numpy()
    Dinnerdata = data['Dinner']
    DinnerdataNumpy = Dinnerdata.to_numpy()
    Food_itemsdata = data['Food_items'].tolist()
    unique_cuisines = data['Cuisine'].unique()

# Helper function to get food by meal type, diet preference, and cuisine
def get_foods_by_meal_preference_and_cuisine(meal_type, veg_preference, cuisine_type=None):
    """
    Get food items based on meal type, vegetarian preference, and cuisine type
    
    Parameters:
    meal_type (str): 'Breakfast', 'Lunch', or 'Dinner'
    veg_preference (int): 1 for vegetarian, 0 for non-vegetarian
    cuisine_type (str): The cuisine type (e.g., 'Italian', 'Indian', etc.) or None for all cuisines
    
    Returns:
    list: List of food items matching criteria
    """
    meal_data = data[meal_type].to_numpy()
    result = []
    
    for i in range(len(meal_data)):
        if meal_data[i] == 1:
            # Check vegetarian preference
            veg_match = (veg_preference == 1 and data['Veg'].iloc[i] == 1) or veg_preference == 0
            
            # Check cuisine type if specified
            cuisine_match = True
            if cuisine_type is not None and cuisine_type != "All":
                cuisine_match = data['Cuisine'].iloc[i] == cuisine_type
            
            # Add if both vegetarian and cuisine requirements match
            if veg_match and cuisine_match:
                result.append(Food_itemsdata[i])
    
    # Fallback if no items found - ignore cuisine to try to get some results
    if not result and cuisine_type is not None and cuisine_type != "All":
        for i in range(len(meal_data)):
            if meal_data[i] == 1:
                # Only check vegetarian preference
                veg_match = (veg_preference == 1 and data['Veg'].iloc[i] == 1) or veg_preference == 0
                if veg_match:
                    result.append(Food_itemsdata[i])
    
    # Ultimate fallback with predefined options
    if not result:
        if meal_type == 'Breakfast':
            if veg_preference == 1:
                result = ["Oatmeal with fruits", "Yogurt with berries", "Avocado Toast"]
            else:
                result = ["Egg white omelet", "Protein shake", "Bacon and eggs"]
        elif meal_type == 'Lunch':
            if veg_preference == 1:
                result = ["Vegetable salad", "Lentil soup", "Quinoa bowl"]
            else:
                result = ["Grilled chicken salad", "Tuna sandwich", "Turkey wrap"]
        else:  # Dinner
            if veg_preference == 1:
                result = ["Vegetable stir-fry", "Tofu curry", "Bean burrito"]
            else:
                result = ["Grilled fish with vegetables", "Chicken stir-fry", "Lean beef with broccoli"]
    
    return result

# Helper function to get cuisine-specific snacks
def get_cuisine_snacks(veg_preference, cuisine_type=None, purpose="healthy"):
    """
    Get snack recommendations based on cuisine, diet preference, and purpose
    
    Parameters:
    veg_preference (int): 1 for vegetarian, 0 for non-vegetarian
    cuisine_type (str): The cuisine type or None for general recommendations
    purpose (str): "healthy", "weight_gain", or "weight_loss"
    
    Returns:
    list: List of snack recommendations
    """
    # Default snacks by cuisine and diet preference
    cuisine_snacks = {
        "Italian": {
            1: ["Bruschetta", "Marinated olives", "Focaccia with olive oil", "Roasted red peppers"],
            0: ["Prosciutto wrapped melon", "Italian meatballs", "Antipasto skewers", "Caprese salad"]
        },
        "Indian": {
            1: ["Roasted chickpeas", "Dhokla", "Chaat", "Bhel puri"],
            0: ["Chicken tikka bites", "Keema samosa", "Tandoori chicken strips", "Fish pakora"]
        },
        "Chinese": {
            1: ["fruit salad", "Spring rolls", "Sesame tofu bites", "Five-spice nuts"],
            0: ["Steamed dumplings", "Honey soy chicken wings", "Char siu pork bites", "Crispy wontons"]
        },
        "Mediterranean": {
            1: ["Hummus with pita", "Stuffed grape leaves", "Falafel", "Greek yogurt with honey"],
            0: ["Tzatziki with grilled meats", "Lamb kofta", "Grilled halloumi", "Seafood skewers"]
        },
        "Mexican": {
            1: ["Guacamole with tortilla chips", "Black bean dip", "Roasted corn", "Jicama sticks"],
            0: ["Chicken taquitos", "Beef jerky", "Mini quesadillas", "Shrimp ceviche"]
        },
        "American": {
            1: ["Trail mix", "Popcorn", "Apple slices with peanut butter", "Celery with hummus"],
            0: ["Beef jerky", "Turkey roll-ups", "Deviled eggs", "Cheese and crackers"]
        },
        "Japanese": {
            1: ["fruit salad", "Cucumber rolls", "Seaweed salad", "Miso soup"],
            0: ["Tuna sashimi", "Chicken yakitori", "Beef tataki", "Shrimp tempura"]
        }
    }
    
    # Weight gain snacks emphasize higher calories
    weight_gain_snacks = {
        "Italian": {
            1: ["Focaccia bread with olive oil", "Nuts and dried fruits mix", "Bruschetta with avocado", "Panzanella"],
            0: ["Arancini", "Meatballs", "Calzone bites", "Stuffed mushrooms"]
        },
        "Indian": {
            1: ["Samosas", "Pakoras", "Aloo tikki", "Peanut chikki"],
            0: ["Chicken pakora", "Kathi rolls", "Malai tikka", "Butter chicken bites"]
        },
        "Chinese": {
            1: ["Sesame balls", "Fried rice", "Vegetable dumplings", "Sweet bean buns"],
            0: ["Char siu bao", "Soy glazed chicken wings", "Peking duck rolls", "Honey walnut prawns"]
        },
        "Mediterranean": {
            1: ["Falafel with tahini", "Spanakopita", "Stuffed dates", "Baklava"],
            0: ["Souvlaki skewers", "Lamb kofta", "Moussaka bites", "Shawarma wraps"]
        },
        "Mexican": {
            1: ["Nachos with cheese", "Bean and cheese quesadillas", "Churros", "Fried plantains"],
            0: ["Loaded nachos", "Chimichangas", "Barbacoa tacos", "Chorizo bites"]
        },
        "American": {
            1: ["Peanut butter sandwich", "Granola bars", "Banana bread", "Mac and cheese bites"],
            0: ["Buffalo wings", "Sliders", "Loaded potato skins", "Meatball subs"]
        },
        "Japanese": {
            1: ["Inari sushi", "Sweet potato tempura", "Rice balls with sesame", "Red bean mochi"],
            0: ["Chicken katsu", "Teriyaki skewers", "Gyoza", "Tonkatsu"]
        }
    }
    
    # Weight loss snacks emphasize lower calories, high protein and fiber
    weight_loss_snacks = {
        "Italian": {
            1: ["Raw vegetables with balsamic vinegar", "Tomato and basil salad", "Grilled zucchini", "Minestrone soup"],
            0: ["Grilled chicken with lemon", "Fish carpaccio", "Light caprese", "Vegetable frittata"]
        },
        "Indian": {
            1: ["Cucumber raita", "Sprout salad", "Roasted chickpeas", "Moong dal soup"],
            0: ["Tandoori chicken strips", "Fish tikka", "Egg bhurji", "Chicken shorba"]
        },
        "Chinese": {
            1: ["Steamed vegetables", "Cucumber salad", "Clear soup", "Steamed tofu"],
            0: ["Steamed fish", "Clear chicken soup", "Lettuce wraps", "Sashimi"]
        },
        "Mediterranean": {
            1: ["Greek salad", "Cucumber sticks", "Lemon broth", "Pickled vegetables"],
            0: ["Grilled fish", "Chicken souvlaki", "Lean meat skewers", "Seafood salad"]
        },
        "Mexican": {
            1: ["Jicama sticks", "Pico de gallo", "Cucumber with chili", "Nopal salad"],
            0: ["Ceviche", "Grilled chicken strips", "Fajita lettuce wraps", "Clear tortilla soup"]
        },
        "American": {
            1: ["Celery sticks", "Cucumber slices", "Vegetable soup", "Air-popped popcorn"],
            0: ["Turkey roll-ups", "Tuna salad on cucumber", "Egg white bites", "Chicken broth"]
        },
        "Japanese": {
            1: ["Cucumber rolls", "Seaweed salad", "Clear miso soup", "Pickled vegetables"],
            0: ["Sashimi", "Clear dashi soup", "Grilled chicken skewers", "Steamed fish"]
        }
    }
    
    # Select appropriate snack collection based on purpose
    if purpose == "weight_gain":
        snack_collection = weight_gain_snacks
    elif purpose == "weight_loss":
        snack_collection = weight_loss_snacks
    else:  # healthy
        snack_collection = cuisine_snacks
    
    # If cuisine specified and available, use it
    if cuisine_type and cuisine_type != "All" and cuisine_type in snack_collection:
        return snack_collection[cuisine_type][veg_preference]
    
    # Otherwise, create a mix of snacks from different cuisines
    mixed_snacks = []
    for cuisine in snack_collection:
        mixed_snacks.extend(snack_collection[cuisine][veg_preference][:1])  # Take one snack from each cuisine
        if len(mixed_snacks) >= 4:
            break
    
    # Fallback to general recommendations if no specific cuisines available
    if not mixed_snacks:
        if purpose == "weight_gain":
            if veg_preference == 1:
                return ["Protein shake with fruits", "Peanut butter sandwich", "Trail mix", "Nuts and dried fruits"]
            else:
                return ["Protein shake with milk", "Beef jerky", "Chicken wrap", "Tuna sandwich"]
        elif purpose == "weight_loss":
            if veg_preference == 1:
                return ["Vegetable sticks", "Cucumber slices", "Berries", "Low-fat yogurt"]
            else:
                return ["Vegetable sticks", "Low-fat yogurt", "Boiled egg whites", "Turkey slices"]
        else:  # healthy
            if veg_preference == 1:
                return ["Greek yogurt", "Fruit bowl", "Mixed nuts", "Hummus with veggie sticks"]
            else:
                return ["Greek yogurt", "Cottage cheese", "Hard-boiled eggs", "Turkey slices"]
    
    return mixed_snacks

# Function 1: Weight Gain Recommendation
def Weight_Gain(age, veg, weight, height, cuisine=None):
    try:
        # Get foods by meal type, vegetarian preference, and cuisine
        breakfast_foods = get_foods_by_meal_preference_and_cuisine('Breakfast', veg, cuisine)
        lunch_foods = get_foods_by_meal_preference_and_cuisine('Lunch', veg, cuisine)
        dinner_foods = get_foods_by_meal_preference_and_cuisine('Dinner', veg, cuisine)
        
        # BMI Calculation
        bmi = weight / ((height / 100) ** 2)

        # Classifying BMI
        if (bmi < 16):
            clbmi = 4
        elif (bmi >= 16 and bmi < 18.5):
            clbmi = 3
        elif (bmi >= 18.5 and bmi < 25):
            clbmi = 2
        elif (bmi >= 25 and bmi < 30):
            clbmi = 1
        elif (bmi >= 30):
            clbmi = 0
            
        # For weight gain, prioritize higher calorie foods
        recommended_food = []
        
        # Select more calorie-dense foods if available
        try:
            # Get calorie information for foods
            breakfast_calories = []
            lunch_calories = []
            dinner_calories = []
            
            for food in breakfast_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0 and 'Calories' in data.columns:
                    calories = data['Calories'].iloc[idx]
                    breakfast_calories.append((food, calories))
                else:
                    # If no calorie info, assume medium value
                    breakfast_calories.append((food, 300))
            
            for food in lunch_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0 and 'Calories' in data.columns:
                    calories = data['Calories'].iloc[idx]
                    lunch_calories.append((food, calories))
                else:
                    lunch_calories.append((food, 500))
                
            for food in dinner_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0 and 'Calories' in data.columns:
                    calories = data['Calories'].iloc[idx]
                    dinner_calories.append((food, calories))
                else:
                    dinner_calories.append((food, 600))
            
            # Sort by calories (descending)
            breakfast_calories.sort(key=lambda x: x[1], reverse=True)
            lunch_calories.sort(key=lambda x: x[1], reverse=True)
            dinner_calories.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 3 from each category
            for i in range(min(3, len(breakfast_calories))):
                recommended_food.append(breakfast_calories[i][0])
                
            for i in range(min(3, len(lunch_calories))):
                recommended_food.append(lunch_calories[i][0])
                
            for i in range(min(3, len(dinner_calories))):
                recommended_food.append(dinner_calories[i][0])
        except Exception as e:
            print(f"Error sorting by calories: {e}")
            # Fallback to random selection
            recommended_food = []
            for i in range(min(3, len(breakfast_foods))):
                recommended_food.append(breakfast_foods[i])
                
            for i in range(min(3, len(lunch_foods))):
                recommended_food.append(lunch_foods[i])
                
            for i in range(min(3, len(dinner_foods))):
                recommended_food.append(dinner_foods[i])
        
        # Add snacks (high protein/calorie) based on cuisine
        snack_options = get_cuisine_snacks(veg, cuisine, "weight_gain")
        
        # Add 3 snack options to get total of 12 items
        for i in range(min(3, len(snack_options))):
            recommended_food.append(snack_options[i])

        # Make sure we have exactly 12 items
        while len(recommended_food) < 12:
            # Add more items if we don't have enough
            if veg == 1:
                recommended_food.append(["Quinoa", "Brown rice", "Oatmeal", "Protein bar"][len(recommended_food) % 4])
            else:
                recommended_food.append(["Chicken", "Eggs", "Salmon", "Steak"][len(recommended_food) % 4])
        
        return recommended_food[:12]  # Return exactly 12 items
    
    except Exception as e:
        print(f"Error in Weight_Gain function: {e}")
        # Return default recommendations if something goes wrong
        if veg == 1:  # Vegetarian
            return ["Oatmeal with fruits", "Avocados", "Yogurt with berries",
                   "Peanut butter sandwich", "Quinoa bowl", "Bean burrito",
                   "Vegetable stir-fry with tofu", "Lentil soup", "Pasta with sauce",
                   "Protein shake with fruits", "Trail mix", "Avocado toast"]
        else:  # Non-vegetarian
            return ["Egg white omelet", "Protein shake", "Bacon and eggs",
                   "Grilled chicken with rice", "Salmon with sweet potatoes", "Tuna sandwich", 
                   "Steak with vegetables", "Chicken stir-fry", "Pasta with meat sauce",
                   "Protein shake with milk", "Beef jerky", "Chicken wrap"]


# Function 2: Healthy Recommendation
def Healthy(age, veg, weight, height, cuisine=None):
    try:
        # Get foods by meal type, vegetarian preference, and cuisine
        breakfast_foods = get_foods_by_meal_preference_and_cuisine('Breakfast', veg, cuisine)
        lunch_foods = get_foods_by_meal_preference_and_cuisine('Lunch', veg, cuisine)
        dinner_foods = get_foods_by_meal_preference_and_cuisine('Dinner', veg, cuisine)
        
        # BMI Calculation
        bmi = weight / ((height / 100) ** 2)

        # Classifying BMI
        if (bmi < 16):
            clbmi = 4
        elif (bmi >= 16 and bmi < 18.5):
            clbmi = 3
        elif (bmi >= 18.5 and bmi < 25):
            clbmi = 2
        elif (bmi >= 25 and bmi < 30):
            clbmi = 1
        elif (bmi >= 30):
            clbmi = 0
            
        # For healthy eating, prioritize balanced nutrition
        recommended_food = []
        
        # Select balanced foods
        try:
            # Get nutrition information for foods
            breakfast_scores = []
            lunch_scores = []
            dinner_scores = []
            
            for food in breakfast_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0:
                    # Calculate nutrition score (prioritize protein and fiber, limit fats and sugars)
                    protein = data['Proteins'].iloc[idx] if 'Proteins' in data.columns else 0
                    fiber = data['Fibre'].iloc[idx] if 'Fibre' in data.columns else 0
                    fat = data['Fats'].iloc[idx] if 'Fats' in data.columns else 0
                    sugar = data['Sugars'].iloc[idx] if 'Sugars' in data.columns else 0
                    
                    score = protein + fiber - (0.5 * fat) - (0.7 * sugar)
                    breakfast_scores.append((food, score))
                else:
                    # Default score if not found
                    breakfast_scores.append((food, 5))
            
            for food in lunch_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0:
                    protein = data['Proteins'].iloc[idx] if 'Proteins' in data.columns else 0
                    fiber = data['Fibre'].iloc[idx] if 'Fibre' in data.columns else 0
                    fat = data['Fats'].iloc[idx] if 'Fats' in data.columns else 0
                    sugar = data['Sugars'].iloc[idx] if 'Sugars' in data.columns else 0
                    
                    score = protein + fiber - (0.5 * fat) - (0.7 * sugar)
                    lunch_scores.append((food, score))
                else:
                    lunch_scores.append((food, 5))
                
            for food in dinner_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0:
                    protein = data['Proteins'].iloc[idx] if 'Proteins' in data.columns else 0
                    fiber = data['Fibre'].iloc[idx] if 'Fibre' in data.columns else 0
                    fat = data['Fats'].iloc[idx] if 'Fats' in data.columns else 0
                    sugar = data['Sugars'].iloc[idx] if 'Sugars' in data.columns else 0
                    
                    score = protein + fiber - (0.5 * fat) - (0.7 * sugar)
                    dinner_scores.append((food, score))
                else:
                    dinner_scores.append((food, 5))
            
            # Sort by nutrition score (descending)
            breakfast_scores.sort(key=lambda x: x[1], reverse=True)
            lunch_scores.sort(key=lambda x: x[1], reverse=True)
            dinner_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 3 from each category
            for i in range(min(3, len(breakfast_scores))):
                recommended_food.append(breakfast_scores[i][0])
                
            for i in range(min(3, len(lunch_scores))):
                recommended_food.append(lunch_scores[i][0])
                
            for i in range(min(3, len(dinner_scores))):
                recommended_food.append(dinner_scores[i][0])
        except Exception as e:
            print(f"Error sorting by nutrition: {e}")
            # Fallback to random selection
            recommended_food = []
            for i in range(min(3, len(breakfast_foods))):
                recommended_food.append(breakfast_foods[i])
                
            for i in range(min(3, len(lunch_foods))):
                recommended_food.append(lunch_foods[i])
                
            for i in range(min(3, len(dinner_foods))):
                recommended_food.append(dinner_foods[i])
        
        # Add healthy snacks based on cuisine
        snack_options = get_cuisine_snacks(veg, cuisine, "healthy")
        
        # Add 3 snack options to get total of 12 items
        for i in range(min(3, len(snack_options))):
            recommended_food.append(snack_options[i])

        # Make sure we have exactly 12 items
        while len(recommended_food) < 12:
            # Add more items if we don't have enough
            if veg == 1:
                recommended_food.append(["Apple", "Orange", "Berries", "Almonds"][len(recommended_food) % 4])
            else:
                recommended_food.append(["Apple", "Orange", "Berries", "Tuna"][len(recommended_food) % 4])
        
        return recommended_food[:12]  # Return exactly 12 items
    
    except Exception as e:
        print(f"Error in Healthy function: {e}")
        # Return default recommendations if something goes wrong
        if veg == 1:  # Vegetarian
            return ["Oatmeal with fruits", "Yogurt with berries", "Avocado Toast",
                   "Vegetable salad", "Lentil soup", "Quinoa bowl", 
                   "Vegetable stir-fry", "Tofu curry", "Bean burrito",
                   "Greek yogurt", "Fruit bowl", "Mixed nuts"]
        else:  # Non-vegetarian
            return ["Egg white omelet", "Yogurt with berries", "Whole grain toast",
                   "Grilled chicken salad", "Turkey wrap", "Tuna sandwich",
                   "Grilled fish", "Chicken stir-fry", "Lean beef with vegetables",
                   "Greek yogurt", "Cottage cheese", "Hard-boiled eggs"]


# Function 3: Weight Loss Recommendation
def Weight_Loss(age, veg, weight, height, cuisine=None):
    try:
        # Get foods by meal type, vegetarian preference, and cuisine
        breakfast_foods = get_foods_by_meal_preference_and_cuisine('Breakfast', veg, cuisine)
        lunch_foods = get_foods_by_meal_preference_and_cuisine('Lunch', veg, cuisine)
        dinner_foods = get_foods_by_meal_preference_and_cuisine('Dinner', veg, cuisine)
        
        # BMI Calculation
        bmi = weight / ((height / 100) ** 2)

        # Classifying BMI
        if (bmi < 16):
            clbmi = 4
        elif (bmi >= 16 and bmi < 18.5):
            clbmi = 3
        elif (bmi >= 18.5 and bmi < 25):
            clbmi = 2
        elif (bmi >= 25 and bmi < 30):
            clbmi = 1
        elif (bmi >= 30):
            clbmi = 0
            
        # For weight loss, prioritize low calorie foods with high protein
        recommended_food = []
        
        # Select low calorie, high protein foods
        try:
            # Get nutrition information for foods
            breakfast_scores = []
            lunch_scores = []
            dinner_scores = []
            
            for food in breakfast_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0:
                    # Calculate weight loss score (prioritize protein, penalize calories/fat/sugar)
                    calories = data['Calories'].iloc[idx] if 'Calories' in data.columns else 0
                    protein = data['Proteins'].iloc[idx] if 'Proteins' in data.columns else 0
                    fiber = data['Fibre'].iloc[idx] if 'Fibre' in data.columns else 0
                    fat = data['Fats'].iloc[idx] if 'Fats' in data.columns else 0
                    sugar = data['Sugars'].iloc[idx] if 'Sugars' in data.columns else 0
                    
                    score = (protein * 2) + fiber - (0.05 * calories) - (fat) - (sugar)
                    breakfast_scores.append((food, score))
                else:
                    breakfast_scores.append((food, 5))
            
            for food in lunch_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0:
                    calories = data['Calories'].iloc[idx] if 'Calories' in data.columns else 0
                    protein = data['Proteins'].iloc[idx] if 'Proteins' in data.columns else 0
                    fiber = data['Fibre'].iloc[idx] if 'Fibre' in data.columns else 0
                    fat = data['Fats'].iloc[idx] if 'Fats' in data.columns else 0
                    sugar = data['Sugars'].iloc[idx] if 'Sugars' in data.columns else 0
                    
                    score = (protein * 2) + fiber - (0.05 * calories) - (fat) - (sugar)
                    lunch_scores.append((food, score))
                else:
                    lunch_scores.append((food, 5))
                
            for food in dinner_foods:
                idx = Food_itemsdata.index(food) if food in Food_itemsdata else -1
                if idx >= 0:
                    calories = data['Calories'].iloc[idx] if 'Calories' in data.columns else 0
                    protein = data['Proteins'].iloc[idx] if 'Proteins' in data.columns else 0
                    fiber = data['Fibre'].iloc[idx] if 'Fibre' in data.columns else 0
                    fat = data['Fats'].iloc[idx] if 'Fats' in data.columns else 0
                    sugar = data['Sugars'].iloc[idx] if 'Sugars' in data.columns else 0
                    
                    score = (protein * 2) + fiber - (0.05 * calories) - (fat) - (sugar)
                    dinner_scores.append((food, score))
                else:
                    dinner_scores.append((food, 5))
            
            # Sort by weight loss score (descending)
            breakfast_scores.sort(key=lambda x: x[1], reverse=True)
            lunch_scores.sort(key=lambda x: x[1], reverse=True)
            dinner_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 3 from each category
            for i in range(min(3, len(breakfast_scores))):
                recommended_food.append(breakfast_scores[i][0])
                
            for i in range(min(3, len(lunch_scores))):
                recommended_food.append(lunch_scores[i][0])
                
            for i in range(min(3, len(dinner_scores))):
                recommended_food.append(dinner_scores[i][0])
        except Exception as e:
            print(f"Error sorting by weight loss score: {e}")
            # Fallback to random selection
            recommended_food = []
            for i in range(min(3, len(breakfast_foods))):
                recommended_food.append(breakfast_foods[i])
                
            for i in range(min(3, len(lunch_foods))):
                recommended_food.append(lunch_foods[i])
                
            for i in range(min(3, len(dinner_foods))):
                recommended_food.append(dinner_foods[i])
        
        # Add weight loss snacks based on cuisine
        snack_options = get_cuisine_snacks(veg, cuisine, "weight_loss")
        
        # Add 3 snack options to get total of 12 items
        for i in range(min(3, len(snack_options))):
            recommended_food.append(snack_options[i])

        # Make sure we have exactly 12 items
        while len(recommended_food) < 12:
            # Add more items if we don't have enough
            if veg == 1:
                recommended_food.append(["Cucumber", "Tomato", "Celery", "Berries"][len(recommended_food) % 4])
            else:
                recommended_food.append(["Cucumber", "Tomato", "Celery", "Egg whites"][len(recommended_food) % 4])
        
        return recommended_food[:12]  # Return exactly 12 items
    
    except Exception as e:
        print(f"Error in Weight_Loss function: {e}")
        # Return default recommendations if something goes wrong
        if veg == 1:  # Vegetarian
            return ["Oatmeal with berries", "Vegetable smoothie", "Green tea",
                   "Vegetable soup", "Salad with light dressing", "Steamed vegetables",
                   "Vegetable stir-fry with tofu", "Lentil soup", "Grilled vegetables",
                   "Vegetable sticks", "Cucumber slices", "Berries"]
        else:  # Non-vegetarian
            return ["Egg white omelet", "Protein shake", "Greek yogurt",
                   "Grilled chicken breast", "Fish soup", "Turkey breast",
                   "Grilled fish with vegetables", "Chicken stir-fry", "Lean beef with broccoli",
                   "Vegetable sticks", "Low-fat yogurt", "Boiled egg whites"]

        
# Define Flask Routes with cuisine support
@app.route('/weight-gain', methods=['POST'])
def weight_gain():
    try:
        data = request.get_json()
        print("Received data:", data)
        
        age = data.get('age', 30)
        veg = data.get('veg', 1)  # Default to vegetarian
        weight = data.get('weight', 70)
        height = data.get('height', 170)
        cuisine = data.get('cuisine', None)  # Added cuisine parameter
        
        recommended_food = Weight_Gain(age, veg, weight, height, cuisine)
        print(f"Recommended foods (weight gain): {recommended_food[:5]}...")
        
        return jsonify({"recommended_food": recommended_food})
    except Exception as e:
        print(f"Error in weight-gain endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/healthy', methods=['POST'])
def healthy():
    try:
        data = request.get_json()
        print("Received data:", data)
        
        age = data.get('age', 30)
        veg = data.get('veg', 1)  # Default to vegetarian
        weight = data.get('weight', 70)
        height = data.get('height', 170)
        cuisine = data.get('cuisine', None)  # Added cuisine parameter
        
        recommended_food = Healthy(age, veg, weight, height, cuisine)
        print(f"Recommended foods (healthy): {recommended_food[:5]}...")
        
        return jsonify({"recommended_food": recommended_food})
    except Exception as e:
        print(f"Error in healthy endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/weight-loss', methods=['POST'])
def weight_loss():
    try:
        data = request.get_json()
        print("Received data:", data)
        
        age = data.get('age', 30)
        veg = data.get('veg', 1)  # Default to vegetarian
        weight = data.get('weight', 70)
        height = data.get('height', 170)
        cuisine = data.get('cuisine', None)  # Added cuisine parameter
        
        recommended_food = Weight_Loss(age, veg, weight, height, cuisine)
        print(f"Recommended foods (weight loss): {recommended_food[:5]}...")
        
        return jsonify({"recommended_food": recommended_food})
    except Exception as e:
        print(f"Error in weight-loss endpoint: {e}")
        return jsonify({"error": str(e)}), 500

# General prediction endpoint that routes to appropriate function
@app.route('/predict-diet', methods=['POST'])
def predict_diet():
    try:
        data = request.get_json()
        print("Received data for prediction:", data)
        
        age = data.get('age', 30)
        veg = data.get('veg', 1)
        weight = data.get('weight', 70)
        height = data.get('height', 170)
        goal = data.get('goal', 'Healthy')
        cuisine = data.get('cuisine', None)  # Added cuisine parameter
        
        # Route to appropriate function based on goal
        if goal == 'Weight Gain':
            recommended_food = Weight_Gain(age, veg, weight, height, cuisine)
        elif goal == 'Weight Loss':
            recommended_food = Weight_Loss(age, veg, weight, height, cuisine)
        else:  # Default to Healthy
            recommended_food = Healthy(age, veg, weight, height, cuisine)
            
        # Make sure we have enough items to create a complete meal plan
        # Filter out any None values first
        recommended_food = [item for item in recommended_food if item]
        
        # If we still don't have enough items, add more from the food items list
        if len(recommended_food) < 12:
            # Get breakfast, lunch, and dinner items from the dataset
            breakfast_items = []
            lunch_items = []
            dinner_items = []
            
            for i in range(len(Breakfastdata)):
                # Apply cuisine filter if specified
                cuisine_match = True
                if cuisine and cuisine != "All" and 'Cuisine' in data.columns:
                    cuisine_match = data['Cuisine'].iloc[i] == cuisine
                
                if BreakfastdataNumpy[i] == 1 and veg == 1 and data.iloc[i]['Veg'] == 1 and cuisine_match:
                    breakfast_items.append(Food_itemsdata[i])
                elif BreakfastdataNumpy[i] == 1 and veg == 0 and cuisine_match:
                    breakfast_items.append(Food_itemsdata[i])
                    
                if LunchdataNumpy[i] == 1 and veg == 1 and data.iloc[i]['Veg'] == 1 and cuisine_match:
                    lunch_items.append(Food_itemsdata[i])
                elif LunchdataNumpy[i] == 1 and veg == 0 and cuisine_match:
                    lunch_items.append(Food_itemsdata[i])
                    
                if DinnerdataNumpy[i] == 1 and veg == 1 and data.iloc[i]['Veg'] == 1 and cuisine_match:
                    dinner_items.append(Food_itemsdata[i])
                elif DinnerdataNumpy[i] == 1 and veg == 0 and cuisine_match:
                    dinner_items.append(Food_itemsdata[i])
            
            # Fallback options in case filtering fails or returns empty lists
            if not breakfast_items:
                if veg == 1:
                    breakfast_items = ["Oatmeal with fruits", "Yogurt with berries", "Avocado Toast"]
                else:
                    breakfast_items = ["Egg white omelet", "Protein shake", "Chicken and avocado sandwich"]
                    
            if not lunch_items:
                if veg == 1:
                    lunch_items = ["Vegetable salad", "Lentil soup", "Quinoa bowl"]
                else:
                    lunch_items = ["Grilled chicken salad", "Tuna sandwich", "Turkey wrap"]
                    
            if not dinner_items:
                if veg == 1:
                    dinner_items = ["Vegetable stir-fry", "Tofu curry", "Bean burrito"]
                else:
                    dinner_items = ["Grilled fish with vegetables", "Chicken stir-fry", "Lean beef with broccoli"]
            
            # Add snack options based on cuisine and purpose
            snack_purpose = "weight_gain" if goal == "Weight Gain" else "weight_loss" if goal == "Weight Loss" else "healthy"
            snack_items = get_cuisine_snacks(veg, cuisine, snack_purpose)
            
            # If no snacks returned, use fallbacks
            if not snack_items:
                if veg == 1:
                    snack_items = ["Fruit bowl", "Greek yogurt", "Nuts mix", "Hummus with veggie sticks"]
                else:
                    snack_items = ["Protein bar", "Beef jerky", "Cottage cheese", "Hard-boiled eggs"]
            
            # Fill in missing items in the recommended_food list
            while len(recommended_food) < 3:  # Ensure at least 3 breakfast items
                recommended_food.append(breakfast_items[len(recommended_food) % len(breakfast_items)])
                
            while len(recommended_food) < 6:  # Add lunch items until we have 6 total
                recommended_food.append(lunch_items[(len(recommended_food) - 3) % len(lunch_items)])
                
            while len(recommended_food) < 9:  # Add dinner items until we have 9 total
                recommended_food.append(dinner_items[(len(recommended_food) - 6) % len(dinner_items)])
                
            while len(recommended_food) < 12:  # Add snack items until we have 12 total
                recommended_food.append(snack_items[(len(recommended_food) - 9) % len(snack_items)])
        
        # Make sure we have exactly 12 items (trim if more)
        recommended_food = recommended_food[:12]
        
        # Create a diet plan structure
        diet_plan = {
            "breakfast": recommended_food[:3],
            "lunch": recommended_food[3:6],
            "dinner": recommended_food[6:9],
            "snacks": recommended_food[9:12]
        }
            
        return jsonify({
            "success": True,
            "dietPlan": diet_plan,
            "recommendations": recommended_food,
            "cuisine": cuisine if cuisine else "All"
        })
    except Exception as e:
        print(f"Error in predict-diet endpoint: {e}")
        # Provide a fallback diet plan if something goes wrong
        fallback_plan = {
            "breakfast": ["Oatmeal with fruits", "Yogurt with berries", "Avocado Toast"] if veg == 1 else 
                         ["Egg white omelet", "Protein shake", "Chicken and avocado sandwich"],
            "lunch": ["Vegetable salad", "Lentil soup", "Quinoa bowl"] if veg == 1 else 
                     ["Grilled chicken salad", "Tuna sandwich", "Turkey wrap"],
            "dinner": ["Vegetable stir-fry", "Tofu curry", "Bean burrito"] if veg == 1 else
                      ["Grilled fish with vegetables", "Chicken stir-fry", "Lean beef with broccoli"],
            "snacks": ["Fruit bowl", "Greek yogurt", "Nuts mix"] if veg == 1 else
                      ["Protein bar", "Beef jerky", "Cottage cheese"]
        }
        
        fallback_foods = []
        for category in ['breakfast', 'lunch', 'dinner', 'snacks']:
            fallback_foods.extend(fallback_plan[category])
            
        return jsonify({
            "success": True,
            "dietPlan": fallback_plan,
            "recommendations": fallback_foods,
            "cuisine": cuisine if cuisine else "All",
            "note": "Used fallback plan due to error: " + str(e)
        })

# Added new endpoint to get available cuisines
@app.route('/available-cuisines', methods=['GET'])
def available_cuisines():
    try:
        # Return all available cuisines from the dataset
        cuisines_list = unique_cuisines.tolist() if hasattr(unique_cuisines, 'tolist') else list(unique_cuisines)
        cuisines_list.insert(0, "All")  # Add "All" option at the beginning
        
        return jsonify({
            "success": True,
            "cuisines": cuisines_list
        })
    except Exception as e:
        print(f"Error fetching cuisines: {e}")
        # Fallback list of common cuisines
        return jsonify({
            "success": True,
            "cuisines": ["All", "Italian", "Indian", "Chinese", "Mediterranean", "Mexican", "American", "Japanese"],
            "note": "Using fallback cuisine list due to error: " + str(e)
        })

if __name__ == '__main__':
    # Print startup message
    print("Starting Nutrition Planner API...")
    print("Available endpoints:")
    print("  - POST /weight-gain")
    print("  - POST /healthy")
    print("  - POST /weight-loss")
    print("  - POST /predict-diet")
    print("  - GET /available-cuisines")
    
    # Check if cuisine data is available
    if 'Cuisine' in data.columns:
        print(f"Available cuisines: {', '.join(unique_cuisines)}")
    
    # Run the Flask app
    app.run(debug=True)