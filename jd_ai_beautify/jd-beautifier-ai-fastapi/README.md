# Project Setup Instructions


## Install the packages listed in requirements.txt
   ``` pip install -r requirements.txt  ```
   

## Backend API

### Run Command

1. Navigate to the `fastapi_streamlit_app/sqlalchemy` directory:
    ```sh
    cd fastapi_streamlit_app/sqlalchemy/app
    ```
2. Run the following command to start the backend API:
    ```sh
    python app.py
    ```

---

## Frontend

### Run Command

1. Navigate to the `fastapi_streamlit_app/sqlalchemy/app` directory:
    ```sh
    cd fastapi_streamlit_app/sqlalchemy/app_frontend
    ```
2. Run the following command to start the Streamlit app:
    ```sh
    streamlit run app.py
    ```
  
### Docker Compose
 
## Build and Run Backend and Frontend (FastAPI and Streamlit)

1. Navigate to the project root directory:
   ```sh
    cd jd-beautifier-ai-fastapi
   ```

2. Build and start the Docker containers for both the backend and frontend:
    ```sh
      docker-compose up --build
    ```