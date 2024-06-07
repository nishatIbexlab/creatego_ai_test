from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
import re
import json
from django.conf import settings
from openai import OpenAI
import time

# assistant_id = asst_6KDOPPSAFiczPYjvi2ZjXweX

client = OpenAI(api_key=settings.API_KEY)

def JsonExtractor(result):
    # Initialize list to store extracted JSON objects
    extracted_json_objects = []
    # Extract JSON parts using regex
    json_parts = re.findall(r'```json\n({.*?})\n```', result, re.DOTALL)

    # Iterate over extracted JSON parts
    for json_string in json_parts:
        # # Replace null values with the string "null"
        # json_string = json_string.replace('null', '"null"')

        # Parse JSON string to dictionary
        data = json.loads(json_string)
        # print(data)
        # add childwidgets key in json_struct for actual component structure
        if "childwidgets" not in data:
            json_struct = {
                "id":None,
                "name":None,
                "description":None,
                "width":None,
                "height":None,
                "dx":None,
                "dy":None,
                "previewImageUrl":None,
                "createdAt":None,
                "updatedAt":None,
                "isPublic":False,
                }
            json_struct.update({"childwidgets": [data]})
            # print(json_struct)
            
            extracted_json_objects.append(json_struct)
            
        # Append extracted JSON object to the list
        else:
            extracted_json_objects.append(data)

    # Return list of extracted JSON objects
    # print(json_string)
    return extracted_json_objects


class assistant(APIView):
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + settings.API_KEY,
        "OpenAI-Beta": "assistants=v1"
    }
    
    

    # returns message list 
    def get(self, request, *args, **kwargs):
        try:
            t_id = str(request.query_params.get('t_id'))
            thread_messages = client.beta.threads.messages.list(t_id)
        except:
            thread_messages = client.beta.threads.messages.list(
                "thread_H47Tmag9DiKc6C6yriIBqABs")
        

#         print(thread_messages)
#         run = client.beta.threads.runs.retrieve(
#   thread_id='thread_7uY3sPNkXEeYMBBQS5h0xuHn',
#   run_id="run_QgJpM88Pq2iKtAFvJH07yvZR"
# )
#         return Response(run)


        # creating a list of all messages in the thread
        msg_list = []
        for data in thread_messages.data:
            result = data.content[0].text.value
            _result = JsonExtractor(result)
            if _result == []:
                _result = [result]
            msg_list.append(_result)
        
        # returning msg list or thread data
        if not msg_list or msg_list == [[]]:
            return Response(thread_messages.data)
        else:
            return Response(msg_list)

    def post(self, request, *args, **kwargs):
        _msg = request.data.get("msg")
        if _msg == None:
            return Response("msg is required, t_id is optional")
        
        t_id = request.data.get("t_id")
        if t_id == None:
            # prompt for new msg
            text = "Generate the text delimited by triple quotes to such format that" + "if there are multiple components to be generated, you generate them separately as different json objects even if there are multiple components of the same type"
            prompt = text + '\n' + '"""' + _msg + '"""'
            msg = [{"role": "user", "content": prompt}]

            # creating new thread
            thread = client.beta.threads.create(messages=msg)

            # creating run
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id="asst_6KDOPPSAFiczPYjvi2ZjXweX"
            )
        else:    
            #adding new msg to same thread
            thread_message = client.beta.threads.messages.create(
                thread_id=t_id,
                role="user",
                content=_msg,
            )
            
            #creating run
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id="asst_6KDOPPSAFiczPYjvi2ZjXweX"
            )

        # checking run status until completed
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id= run.id
            )
            if run.status == 'completed':
                break
            time.sleep(5) # Wait for five second before checking again

        # getting the thread messages list
        thread_messages = client.beta.threads.messages.list(thread.id)
        msg_list = []
        for data in thread_messages.data:
            result = data.content[0].text.value
            _result = JsonExtractor(result)
            if _result == []:
                _result = [result]
            msg_list.append(_result)
        print(run)        
        return Response(msg_list)
