import instructor
from openai import OpenAI
from schemas import IdeaRecipes

def formatRecipes(recipes: IdeaRecipes):
    """
    Formats the IdeaRecipes object in to a nice, readable format.
    """
    formatted_output = ""
    for i, recipe in enumerate(recipes.recipes, 1):
        formatted_output += f"Recipe {i}:\n"
        formatted_output += f"Description: {recipe.description}\n\n"
        
        formatted_output += "Ingredients:\n"
        for ingredient in recipe.ingredients:
            formatted_output += f"- {ingredient.quantity} {ingredient.item}\n"
        formatted_output += "\n"
        
        formatted_output += "Instructions:\n"
        for step_num, step in enumerate(recipe.instructions, 1):
            formatted_output += f"{step_num}. {step.instruction}\n"
            if step.items:
                formatted_output += f"   Items used: {', '.join(step.items)}\n"
        formatted_output += "\n"
    
    return formatted_output.strip()

if __name__ == "__main__":
    systemPrompt = """Your job is to help a chef prepare meal recipes that they're thinking of. The chef will provide a meal idea, and you will output
some complete recipes for them to shop and follow."""

    mealIdea = "I need some recipes that use grilled chicken. Make them varied, since I'll be eating this twice a day"

    # TODO: get context from exa here from the meal idea
    
    client = instructor.from_openai(OpenAI())
    recipes: IdeaRecipes = client.chat.completions.create(
        model="gpt-4o",
        response_model=IdeaRecipes,
        messages=[
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": mealIdea},
        ],
    )

    formattedRecipes = formatRecipes(recipes)

    print(formattedRecipes)
