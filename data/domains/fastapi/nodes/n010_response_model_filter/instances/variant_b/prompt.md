# response_model memfilter field (varian B)

Buat `app` FastAPI:

- Model input `EmployeeIn`: `name: str`, `salary: int`, `department: str`.
- Model output `EmployeeOut`: `name: str`, `department: str`.
- `POST /employees` dengan **`response_model=EmployeeOut`** dan **status 201**,
  menerima `EmployeeIn`, mengembalikan objek input apa adanya.

`salary` tidak boleh muncul di body respons. Body input tak valid -> **422**.
