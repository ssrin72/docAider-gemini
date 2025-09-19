FROM python:3.10

# Install dependencies
RUN apt-get update && apt-get install -y git graphviz

WORKDIR /docAider

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY autogen_utils ./autogen_utils
COPY cache ./cache
COPY celery_worker ./celery_worker
COPY code2flow ./code2flow
COPY exceptions.py .
COPY rag ./rag
COPY repo_agents ./repo_agents
COPY repo_documentation ./repo_documentation

CMD ["tail", "-f", "/dev/null"]
