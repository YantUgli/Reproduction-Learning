# Body bersarang + list (varian A)

Buat `app` FastAPI:

- Model `Line`: `sku: str`, `qty: int`.
- Model `Order`: `customer: str`, `lines: list[Line]`.
- `POST /orders` (**status 201**) menerima `Order`, kembalikan
  `{"customer": ..., "total_qty": <jumlah qty semua line>}`.

Yang diuji: satu elemen `lines` cacat (mis. `qty` bukan integer) atau `lines`
bukan list -> **422** untuk seluruh request.
