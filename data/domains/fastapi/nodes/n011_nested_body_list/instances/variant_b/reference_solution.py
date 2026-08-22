from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Ingredient(BaseModel):
    name: str
    grams: int


class Recipe(BaseModel):
    title: str
    ingredients: list[Ingredient]


@app.post("/recipes", status_code=201)
def create_recipe(recipe: Recipe):
    return {
        "title": recipe.title,
        "total_grams": sum(item.grams for item in recipe.ingredients),
    }
