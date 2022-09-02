import os
import requests
import gzip
import shutil
import bigjson
from google.cloud import storage
from google.cloud import bigquery
from urllib.parse import urlparse

def convert_json_to_jsonl():

    with open('ADG_dump.json', 'rb') as f:
        json_data = bigjson.load(f)

        with open('output_ADG.jsonl', 'w') as outfile:
            
            for data in json_data:
                dict_data = data.to_python()
                outfile.write(json.dumps(dict_data)+"\n")
                
    print('File converted from json to jsonl')			
			


def upload_to_GCS():

    client = storage.Client(project='springer-nature-analytics')
    bucket = client.get_bucket('sandbox_data_engineering')
    blob = bucket.blob('Author_Data_Graph/new/output_ADG.jsonl')
    with open('output_ADG.jsonl', 'rb') as json_file:
        blob.upload_from_file(json_file)
        
    print('File uploaded to GCS gs://sandbox_data_engineering/Author_Data_Graph/new/ ')		
	

def upload_to_GBQ():

    client = bigquery.Client()
    table_id = "dataeng_sandbox.ADG_Author_data_graph"

    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    
    uri = "gs://sandbox_data_engineering/Author_Data_Graph/new/output_ADG.jsonl"
    load_job = client.load_table_from_uri(
        uri, table_id, job_config=job_config
    )
    load_job.result()
    destination_table = client.get_table(table_id)
    print("Loaded {} rows.".format(destination_table.num_rows))
        
    print('File uploaded to GBQ table dataeng_sandbox.ADG_Author_data_graph ')	


def download_ADG_dump():   
    
    username = 'vikrant.ghadge'
    
    url = 'https://awa.tgho.nl/data/download/person_id_doi/?filtered=true'
    #filename = os.path.basename(urlparse(url).path)
    r = requests.get(url,allow_redirects=True, auth=(username,password))
    if r.status_code == 200:
            with open('dump.gz', 'wb') as out:
                    for bits in r.iter_content():
                            out.write(bits)
    print("Downloaded new dump.gz")          

    with gzip.open('dump.gz', 'rb') as f_in:
            with open('ADG_dump.json', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    
    
    print("Dump extracted to json")    
    
    
    
if __name__=="__main__":    
    
    username = 'vikrant.ghadge'
    url = 'https://awa.tgho.nl/data/current_version/'
    #filename = os.path.basename(urlparse(url).path)
    r = requests.get(url,allow_redirects=True, auth=(username,password))
    x = r.json()['version']

    f = open("version.txt", "r")
    y = f.read()
    #f.close()

    if x!=y:
           

            if os.path.exists("dump.gz"):
                os.remove("dump.gz")
                print("Deleted previous dump.gz")
            if os.path.exists("ADG_dump.json"):
                os.remove("ADG_dump.json")
                print("Deleted previous ADG_dump.json")
            if os.path.exists("output_ADG.jsonl"):
                os.remove("output_ADG.jsonl")
                print("Deleted previous output_ADG.jsonl")
            
            f1 = open("version.txt", "w")
            f1.write(x)
            download_ADG_dump()
            convert_json_to_jsonl()
            upload_to_GCS()
            upload_to_GBQ()
