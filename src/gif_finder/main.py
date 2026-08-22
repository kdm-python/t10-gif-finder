"""Main API entry point for the GIF Finder application."""

from fastapi import FastAPI

from gif_finder.api.gifs import router as gifs_router

app = FastAPI()
app.include_router(gifs_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the GIF Finder API"}


# from gif_finder.database.database import create_db_and_tables

# if __name__ == "__main__":
#     create_db_and_tables()
