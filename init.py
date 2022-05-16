from pathlib import Path
import sys

def register_engine(path: str):
    save_path = Path(__file__).parent / "matcall" / "matcall-info.txt"
    sys.path.append(str(path))
    try:
        import matlab.engine as eng
    except ImportError as e:
        if e.msg == "No module named 'matlab'":
            raise ValueError(
                f"'matlab' module not found at {path!r}. Make sure you've installed"
                "MATLAB API at correct path."
            )
        else:
            raise e
    
    with open(save_path, mode="w") as f:
        f.write(path)

if __name__ == "__main__":
    register_engine(sys.argv[1])