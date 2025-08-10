import inspect
from app.services import gallery_service as gs

funcs = [(n,f) for n,f in vars(gs).items() if inspect.isfunction(f)]
print("== functions in gallery_service ==")
for n,f in funcs:
    try:
        sig = str(inspect.signature(f))
    except Exception:
        sig = "(signature unknown)"
    print(f"- {n}{sig}")
