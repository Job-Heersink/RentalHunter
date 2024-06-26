FROM public.ecr.aws/lambda/python:3.11

LABEL authors="jobheersink"

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY app ${LAMBDA_TASK_ROOT}/app

CMD [ "app.main.handler" ]