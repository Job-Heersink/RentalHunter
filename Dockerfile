FROM public.ecr.aws/lambda/python:3.9

LABEL authors="jobheersink"

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY app ${LAMBDA_TASK_ROOT}/app
#COPY resources ${LAMBDA_TASK_ROOT}/resources

CMD [ "app.main.handler" ]