from pydantic import BaseModel, Field
from typing import List

class Ingredient(BaseModel):
    item: str = Field(..., description="The name of the ingredient. No other text but the ingredient name.")
    unit: str = Field(..., description="The measurement unit. oz, tsp, tbsp, lb, etc.")
    quantity: float = Field(..., description="Quantity of the item as a float.")

class Recipe(BaseModel):
    ingredients: List[Ingredient]
    description: str
    instructions: List[str] = Field(..., description="List of instructions to make this recipe. No numbers are listed here.")
    source: str = Field(..., description="Where the recipe was found. If you created it, leave this blank.")

class IdeaRecipes(BaseModel):
    recipes: List[Recipe]
