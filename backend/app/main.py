from fastapi import FastAPI

app = FastAPI(title="Knowledge Management Platform")


@app.get("/health")
def health_check():
	return {"status": "healthy"}
