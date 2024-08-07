from pydantic import BaseModel
from typing import List

class Ingredient(BaseModel):
    item: str
    quantity: str

class InstructionStep(BaseModel):
    items: List[str]
    instruction: str

class Recipe(BaseModel):
    ingredients: List[Ingredient]
    description: str
    instructions: List[InstructionStep]

class IdeaRecipes(BaseModel):
    recipes: List[Recipe]
