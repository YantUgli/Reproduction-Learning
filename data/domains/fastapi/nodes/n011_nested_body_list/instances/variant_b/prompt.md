# Body bersarang + list (varian B)

Buat `app` FastAPI:

- Model `Ingredient`: `name: str`, `grams: int`.
- Model `Recipe`: `title: str`, `ingredients: list[Ingredient]`.
- `POST /recipes` (**status 201**) menerima `Recipe`, kembalikan
  `{"title": ..., "total_grams": <jumlah grams semua ingredient>}`.

Elemen cacat atau `ingredients` bukan list -> **422**.
