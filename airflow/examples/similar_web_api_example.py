import datetime
import os
import logging

from airflow import DAG
from airflow import models
from airflow.contrib.operators import bigquery_to_gcs
from airflow.contrib.operators import gcs_to_bq
#from airflow.operators import dummy_operator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import BashOperator

# Import operator from plugins
from airflow.contrib.operators import gcs_to_gcs


from airflow.utils import trigger_rule

# Output file for job.
output_file = os.path.join(
    models.Variable.get('gcs_bucket'), 'MyBucket',
    datetime.datetime.now().strftime('%Y%m%d-%H%M%S')) + os.sep
# Path to GCS buckets. no need to add gs://
DST_BUCKET = ('myBucket')
 
yesterday = datetime.datetime.combine(
    datetime.datetime.today() - datetime.timedelta(1),
    datetime.datetime.min.time())

default_dag_args = {
    # Setting start date as yesterday starts the DAG immediately when it is
    # detected in the Cloud Storage bucket.
    'start_date': yesterday,
    # To email on failure or retry set 'email' arg to your email and enable
    # emailing here.
    'email_on_failure': False,
    'email_on_retry': False,
    # If a task fails, retry it once after waiting at least 5 minutes
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
    'project_id': models.Variable.get('gcp_project')
}



dst_table							='DATA_LAKE.similar_web_table'

from datetime import timedelta, date


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


### start & end date = delta period.
## -3 days?
delta=-2 
start_date = datetime.date.today() + datetime.timedelta(delta)
end_date = datetime.date.today()

 
with models.DAG('similar_web_api_pipeline', schedule_interval=None, default_args=default_dag_args) as dag:

	start = DummyOperator(task_id='start')
	wait 	= DummyOperator(task_id='wait')
	
	
	for single_date in daterange(start_date, end_date):
		bash_cmd="""curl --location --request GET 'https://api.similarweb.com/v1/website/big-data-demystified.ninja/traffic-and-engagement/visits?api_key=myApiKey123456789&start_date=2019-11&end_date=2019-11&country=gb&granularity=monthly&main_domain_only=false&format=json' > /tmp/file_"""+single_date.strftime("%Y%m%d")+'.json'	
		bash_api_call_GET_DESKTOP_TRAFFIC = BashOperator(task_id='bash_api_call_GET_DESKTOP_TRAFFIC'+single_date.strftime("%Y%m%d"),bash_command=bash_cmd)
		
		bash_cmd2="""gsutil mv /tmp/file_"""+single_date.strftime("%Y%m%d")+'.json gs://data_lake/similar_web_desktop_traffic/'	
		bash_gsutil_mv_files_to_ingestion = BashOperator(task_id='bash_gsutil_mv_files_to_ingestion'+single_date.strftime("%Y%m%d"),bash_command=bash_cmd2)
		#bash_cmd="""ls"""
		#bash_api_call_GET_DESKTOP_TRAFFIC = BashOperator(task_id='bash_opr_'+str(item),bash_command=bash_cmd)
		start.set_downstream(bash_api_call_GET_DESKTOP_TRAFFIC)
		bash_api_call_GET_DESKTOP_TRAFFIC.set_downstream(bash_gsutil_mv_files_to_ingestion)
		bash_gsutil_mv_files_to_ingestion.set_downstream(wait)

				
	load_to_bg_GET_DESKTOP_TRAFFIC = gcs_to_bq.GoogleCloudStorageToBigQueryOperator(
    	task_id='load_to_bg_GET_DESKTOP_TRAFFIC',
    	source_objects=['*'],
     	write_disposition='WRITE_TRUNCATE', #overwrite?
    	create_disposition='CREATE_IF_NEEDED',
    	bucket=DST_BUCKET,
    	destination_project_dataset_table=dst_table,
    	autodetect='true')

	end 	= DummyOperator(task_id='end')

wait 	>> load_to_bg_GET_DESKTOP_TRAFFIC 	>> end
