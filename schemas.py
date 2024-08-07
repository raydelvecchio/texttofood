from pydantic import BaseModel, Field
from typing import List, Optional

class Ingredient(BaseModel):
    item: str = Field(..., description="The name of the ingredient. No other text but the ingredient name. Reduce the ingredient name to the simplest form (instead of `boneless skinless chicken breast`, just say `chicken breast`)")
    unit: Optional[str] = Field(..., description="The measurement unit. oz, tsp, tbsp, lb, etc. If there is no unit, this should be None.")
    quantity: Optional[float] = Field(..., description="Quantity of the item as a float.")

class Recipe(BaseModel):
    title: str
    description: str
    ingredients: List[Ingredient]
    instructions: List[str] = Field(..., description="List of instructions to make this recipe. No numbers are listed here.")
    source: str = Field(..., description="Where the recipe was found. If you created it, leave this blank.")

class IdeaRecipes(BaseModel):
    recipes: List[Recipe]

class MealIdeas(BaseModel):
    ideas: List[str] = Field(..., max_length=5, description="List of up to 5 general meal ideas for the user. No numbers listed here.")
