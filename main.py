import instructor
from openai import OpenAI
from schemas import IdeaRecipes
from typing import List
from exa_py import Exa
import os
from dotenv import load_dotenv
load_dotenv()

def formatRecipes(recipes: IdeaRecipes):
    """
    Formats the IdeaRecipes object into a nice, readable format.
    """
    formatted_output = ""
    for i, recipe in enumerate(recipes.recipes, 1):
        formatted_output += f"Recipe {i}:\n"
        formatted_output += f"Description: {recipe.description}\n\n"
        
        formatted_output += "Ingredients:\n"
        for ingredient in recipe.ingredients:
            quantity = int(ingredient.quantity) if ingredient.quantity.is_integer() else ingredient.quantity
            formatted_output += f"- {quantity} {ingredient.unit} {ingredient.item}\n"
        formatted_output += "\n"
        
        formatted_output += "Instructions:\n"
        for step_num, instruction in enumerate(recipe.instructions, 1):
            formatted_output += f"{step_num}. {instruction}\n"
        formatted_output += "\n"
        
        if recipe.source:
            formatted_output += f"Source: {recipe.source}\n\n"
    
    return formatted_output.strip()

def formatExaResults(results: List[any]) -> str:
    """
    Formats the exa results in a way that we want to display it to the LLM.
    """
    formatted_results = ""
    for result in results:
        formatted_results += f"URL: {result.url}\n\n"
        formatted_results += f"Text: {result.text}\n\n"
        formatted_results += "\n\n"
    return formatted_results.strip()

if __name__ == "__main__":
    systemPrompt = """Your job is to help a chef prepare meal recipes that they're thinking of. The chef will provide a meal idea, and you will output
some complete recipes for them to shop and follow. You may also receive some context of the chef's own research. If this context is present,
then you should use it to help create recipes!"""

    mealIdea = "some tasty grilled chicken recipes"

    exa = Exa(api_key=os.getenv("EXA_API_KEY"))

    result = exa.search_and_contents(
        mealIdea,
        type="neural",
        use_autoprompt=True,
        num_results=5,
    )

    formattedResults = formatExaResults(result.results)
    
    client = instructor.from_openai(OpenAI())
    recipes: IdeaRecipes = client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=IdeaRecipes,
        messages=[
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": f"Meal Idea: {mealIdea}\n\nContext:\n{formattedResults}"},
        ],
    )

    formattedRecipes = formatRecipes(recipes)

    print(formattedRecipes)
