import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Body, responses, status
from fastapi import Depends, FastAPI
from openai import OpenAI
from db import User, create_db_and_tables, JobDescription, get_async_session
from schemas import UserCreate, UserRead, UserUpdate, JobDescriptionRequest, BeautifiedJobDescriptionResponse, \
    JobDescriptionResponse
from users import auth_backend, current_active_user, fastapi_users
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import session
from sqlalchemy import select,text
from  db import engine,async_session_maker
from sqlalchemy.exc import OperationalError
from fastapi.middleware.cors import CORSMiddleware





load_dotenv()

### Prompt Concepts ##

job_description_template_prompt = """
**Job Title: [Enter Job Title]**

**Position Summary:**
[Provide a concise summary of the position. What is the primary purpose of this role within the organization?]

**Job Responsibilities:**
- [List the primary duties and tasks expected of the individual in this role. Use bullet points for clarity.]

**Required and/or Preferred Qualifications:**
- Education: [Specify required and/or preferred education levels or degrees.]
- Experience: [Detail required and/or preferred years of experience in relevant fields.]
- Licenses: [Mention any necessary licenses or certifications.]
- Skills: [Outline required and/or preferred skills and competencies.]

**Preferred:**
- [Include any additional qualifications, characteristics, or experiences that would be advantageous but are not mandatory.]

**Why Join Us?**
[Explain why the candidate should consider joining your organization. Highlight unique aspects of your company culture, values, growth opportunities, etc.]

**What We Offer:**
- [Describe the benefits of working at your organization, such as competitive salary, opportunities for professional development, work-life balance, company culture, etc.]
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield




app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# app.include_router(
#     fastapi_users.get_oauth_router(google_oauth_client, auth_backend, SECRET),
#     prefix="/auth/google",
#     tags=["auth"],
# )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://0.0.0.0:8051"],  # Adjust as per your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)





# @app.get("/check-db")
# async def check_db(session: AsyncSession = Depends(async_session_maker)):
#     result = await session.execute(text("SELECT 1"))
#     return {"status": "Database is connected", "result": result.scalar()}


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


@app.post("/beautify_job_description", response_model=BeautifiedJobDescriptionResponse)
async def beautify_job_description(
        request: JobDescriptionRequest,
        user: User = Depends(fastapi_users.current_user(active=True, verified=False)),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        prompt = f"Job Description: {request.job_description}\nRole: {request.role}\nExperience: {request.experience}\nLocation: {request.location}\n"
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": job_description_template_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3800,
            n=3,
            stop=None,
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        beautified_description = [choice.message.content.strip() for choice in response.choices]

        new_job = JobDescription(
            job_description=request.job_description,
            role=request.role,
            experience=request.experience,
            location=request.location,
            beautified_description_1=beautified_description[0],
            beautified_description_2=beautified_description[1],
            beautified_description_3=beautified_description[2],
            user_id=user.id
        )
        session.add(new_job)
        await session.commit()
        await session.refresh(new_job)

        return {"beautified_job_description": beautified_description[0:3]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# Job history details

@app.get("/job_description_history", response_model=list[JobDescriptionResponse])
async def get_job_description_history(user: User = Depends(fastapi_users.current_user(active=True, verified=False)),
                                      session: AsyncSession = Depends(get_async_session)):
    try:
        # Retrieve all job descriptions associated with the current user
        job_descriptions = await session.execute(select(JobDescription).filter_by(user_id=user.id))
        job_description_history = job_descriptions.scalars().all()

        return job_description_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.delete("/job_description/{job_id}", response_model=JobDescriptionResponse)
async def delete_job_description(job_id: int,
                                 user: User = Depends(fastapi_users.current_user(active=True, verified=False)),
                                 session: AsyncSession = Depends(get_async_session)):
    try:

        job_description = await session.execute(select(JobDescription).filter_by(id=job_id, user_id=user.id))
        job = job_description.scalars().first()

        if not job:
            raise HTTPException(status_code=404, detail="Job Description not found")

        session.delete(job)
        await session.commit()
        return job

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.put("/job_description/{job_id}/rename", response_model=JobDescriptionResponse)
async def rename_job_description(job_id: int, new_name=str,
                           user: User = Depends(fastapi_users.current_user(active=True, verified=False)),
                           session: AsyncSession = Depends(get_async_session)
                           ):
    try:
        job_description = await session.execute(select(JobDescription).filter_by(id=job_id, user_id=user.id))
        job = job_description.scalars().first()

        if not job:
            raise HTTPException(status_code=404, detail="Job Description not found")

        job.role = new_name
        await session.commit()

        return job

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



#archive job description

@app.put("/job_description/{job_id}/archive", response_model=JobDescriptionResponse)
async def  archive_job_description(
        job_id: int,
        user:User=Depends(fastapi_users.current_user(active=True,verified=False)),
        session:AsyncSession=Depends(get_async_session)):



    try:


        job_description = await session.execute(select(JobDescription).filter_by(id=job_id,user_id=user.id))
        job = job_description.scalars().first()

        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")

        job.archived = True
        await session.commit()

        return job

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")






import uvicorn
if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", log_level="info",reload=True)
