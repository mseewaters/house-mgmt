# Open CORS configuration without credentials
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# No credentials: Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK with allow_credentials=False
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)