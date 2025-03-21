from fastapi import FastAPI
from app.routers import questions, chat, analysis, answers
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="ReuniCheck API", version="1.0")
print("hola print")
# Incluir routers

app.include_router(answers.router)
app.include_router(questions.router)
app.include_router(chat.router)
app.include_router(analysis.router)

@app.get("/")
def root():
    return {"message": "Hola Mundooo"}
# CORS middleware example
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
