import instructor
from openai import AsyncOpenAI
from schemas import IdeaRecipes, MealIdeas, Recipe
from typing import List, Dict
import httpx
import os
import time
from dotenv import load_dotenv
import asyncio
load_dotenv()

def formatRecipe(recipe: Recipe):
    """
    Formats a single Recipe object into a nice, readable format.
    """
    formattedOutput = ""
    formattedOutput += f"Recipe: {recipe.title}\n"
    formattedOutput += f"Description: {recipe.description}\n\n"
    
    formattedOutput += "Ingredients:\n"
    for ingredient in recipe.ingredients:
        if ingredient.quantity is not None:
            quantity = int(ingredient.quantity) if ingredient.quantity.is_integer() else ingredient.quantity
            if ingredient.unit:
                formattedOutput += f"- {quantity} {ingredient.unit} {ingredient.item}\n"
            else:
                formattedOutput += f"- {quantity} {ingredient.item}\n"
        else:
            if ingredient.unit:
                formattedOutput += f"- {ingredient.unit} {ingredient.item}\n"
            else:
                formattedOutput += f"- {ingredient.item}\n"
    formattedOutput += "\n"
    
    formattedOutput += "Instructions:\n"
    for stepNum, instruction in enumerate(recipe.instructions, 1):
        formattedOutput += f"{stepNum}. {instruction}\n"
    formattedOutput += "\n"
    
    if recipe.source:
        formattedOutput += f"Source: {recipe.source}\n"
    
    return formattedOutput.strip()

def formatExaResults(results: List[dict]) -> str:
    """
    Formats the exa results in a way that we want to display it to the LLM.
    """
    formattedResults = ""
    for result in results:
        formattedResults += f"URL: {result["url"]}\n\n"
        formattedResults += f"Author: {result["author"]}\n\n"
        formattedResults += f"Text: {result["text"]}\n\n"
        formattedResults += "\n\n"
    return formattedResults.strip()

async def searchExa(query: str) -> List[dict]:
    """
    Performs an asynchronous search using the Exa API.
    """
    url = "https://api.exa.ai/search"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": os.getenv("EXA_API_KEY")
    }
    data = {
        "query": query,
        "type": "neural",
        "useAutoprompt": True,
        "numResults": 5,
        "contents": {
            "text": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["results"]

async def getRecipes(idea: str) -> IdeaRecipes:
    """
    Gets recipes for an idea all async.
    """
    systemPrompt = """Your job is to help a chef prepare meal recipes that they're thinking of. The chef will provide a meal idea, and you will output
some complete recipes for them to shop and follow. You may also receive some context of the chef's own research. If this context is present,
then you should use it to help create recipes!"""

    results = await searchExa(idea)
    formattedResults = formatExaResults(results)
    
    client = instructor.apatch(AsyncOpenAI())  
    recipes: IdeaRecipes = await client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=IdeaRecipes,
        messages=[
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": f"Meal Idea: {idea}\n\nContext:\n{formattedResults}"},
        ],
    )

    return recipes

async def getMealIdeas(seedContext: str) -> MealIdeas:
    """
    Given some context seeded by the user, get a list of meal ideas that would be ideal for them.
    """
    systemPrompt = """Your job is to help a user figure out what to eat. You will receive some context from the user about what they're looking for in their food,
and you will split it up into discrete GENERAL CATEGORIES. Do not get too specific with each meal.

EXAMPLES

CONTEXT: 
"My personal trainer told me I need to eat more protein. I have to eat 2 cups of chicken a day, and 1 cup of greek yogurt. I think the yogurt would be good with some honey, blueberries, and granola. Perhaps some quesadillas for the chicken too?"
OUTPUT:
tasty grilled chicken meals, chicken quesadilla, greek yogurt with honey and fruit, parfait breakfast
"""

    client = instructor.apatch(AsyncOpenAI())  
    meals: MealIdeas = await client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=MealIdeas,
        messages=[
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": seedContext},
        ],
    )

    return meals

def getShoppingList(allRecipes: List[Recipe]) -> Dict[str, Dict[str, float]]:
    """
    Generate a shopping list from a list of recipes.

    Args:
    allRecipes (List[Recipe]): A list of Recipe objects.

    Returns:
    Dict[str, Dict[str, float]]: A dictionary representing the shopping list.
    The keys are ingredient names (with units if applicable),
    and the values are dictionaries containing 'quantity' and 'unit'.
    """
    shoppingList = {}
    for recipe in allRecipes:
        for ingredient in recipe.ingredients:
            key = ingredient.item
            if ingredient.unit:
                key = f"{ingredient.item} ({ingredient.unit})"
            
            if key not in shoppingList:
                shoppingList[key] = {
                    "quantity": ingredient.quantity or 0,
                    "unit": ingredient.unit
                }
            else:
                if shoppingList[key]["unit"] == ingredient.unit:
                    shoppingList[key]["quantity"] += (ingredient.quantity or 0)
                else:
                    newKey = f"{ingredient.item} ({ingredient.unit})"
                    shoppingList[newKey] = {
                        "quantity": ingredient.quantity or 0,
                        "unit": ingredient.unit
                    }
    
    # Remove items with zero quantity
    shoppingList = {k: v for k, v in shoppingList.items() if v["quantity"] > 0}
    
    return shoppingList

async def main():
    start_time = time.time()

    context = "I have to eat 2 cups of chicken a day, and 1 cup of greek yogurt. Maybe some quesadillas with chicken would be nice too"
    ideas = await getMealIdeas(context)

    allRecipes = []
    async def fetchRecipes(idea):
        recipes = await getRecipes(idea)
        return recipes.recipes

    recipeTasks = [fetchRecipes(idea) for idea in ideas.ideas]
    recipeResults = await asyncio.gather(*recipeTasks)
    
    for result in recipeResults:
        allRecipes.extend(result)
    
    recipeFolderName = f"recipes_{int(asyncio.get_event_loop().time())}"
    os.makedirs(recipeFolderName)

    for recipe in allRecipes:
        filename = "".join(c if c.isalnum() or c in (" ", "-") else "_" for c in recipe.title)
        filename = filename.replace(" ", "_") + ".txt"
        filepath = os.path.join(recipeFolderName, filename)
        
        formattedRecipe = formatRecipe(recipe)
        with open(filepath, "w") as f:
            f.write(formattedRecipe)
    
    shoppingList = getShoppingList(allRecipes)

    with open(f"{recipeFolderName}/SHOPPINGLIST.txt", "w") as f:
        f.write("Shopping List:\n\n")
        for item, details in shoppingList.items():
            if details["unit"]:
                f.write(f"{item}: {details['quantity']} {details['unit']}\n")
            else:
                f.write(f"{item}: {details['quantity']}\n")

    print("Created SHOPPINGLIST.txt with all ingredients and their summed amounts.")
    print(f"Created {len(allRecipes)} recipe files in the 'recipes' folder.")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
