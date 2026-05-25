from pydantic import BaseModel, Field

class DBCredentials(BaseModel):
    user: str = Field(alias="username")
    password: str
    host: str
    database: str = Field(default="postgres", alias="dbname")
    port: int = 5432

    model_config = {"populate_by_name": True}